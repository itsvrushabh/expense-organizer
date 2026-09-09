use crate::queue::QueueManager;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncResult {
    pub success: bool,
    pub total_pending: usize,
    pub synced_count: usize,
    pub failed_count: usize,
    pub remaining_pending: usize,
    pub errors: Vec<String>,
}

pub fn check_online(api_url: &str, timeout_ms: u64) -> bool {
    let clean_url = api_url.trim().trim_end_matches('/');
    let target = format!("{clean_url}/");
    let agent = ureq::AgentBuilder::new()
        .timeout(Duration::from_millis(timeout_ms))
        .build();

    match agent.get(&target).call() {
        Ok(res) => (200..300).contains(&res.status()),
        Err(_) => false,
    }
}

pub fn sync_pending_queue(queue_manager: &QueueManager, api_url: &str) -> SyncResult {
    let clean_url = api_url.trim().trim_end_matches('/');
    let pending_items = match queue_manager.get_pending_items() {
        Ok(items) => items,
        Err(e) => {
            return SyncResult {
                success: false,
                total_pending: 0,
                synced_count: 0,
                failed_count: 0,
                remaining_pending: 0,
                errors: vec![format!("Failed to read queue: {e}")],
            };
        }
    };

    let total = pending_items.len();
    if total == 0 {
        return SyncResult {
            success: true,
            total_pending: 0,
            synced_count: 0,
            failed_count: 0,
            remaining_pending: 0,
            errors: Vec::new(),
        };
    }

    let agent = ureq::AgentBuilder::new()
        .timeout(Duration::from_secs(8))
        .build();

    let post_endpoint = format!("{clean_url}/expenses");
    let mut synced = 0;
    let mut failed = 0;
    let mut errors = Vec::new();

    for item in pending_items {
        let payload = json!({
            "description": item.description,
            "amount": item.amount,
            "category": item.category,
            "date": item.date,
        });

        match agent.post(&post_endpoint).send_json(payload) {
            Ok(res) if (200..300).contains(&res.status()) => {
                if let Err(e) = queue_manager.mark_synced(&item.id) {
                    errors.push(format!(
                        "Synced on server but failed to update local state: {e}"
                    ));
                }
                synced += 1;
            }
            Ok(res) => {
                let err_msg = format!("HTTP error {} for item {}", res.status(), item.id);
                let _ = queue_manager.mark_failed(&item.id, &err_msg);
                errors.push(err_msg);
                failed += 1;
            }
            Err(e) => {
                let err_msg = format!("Network error sending item {}: {}", item.id, e);
                let _ = queue_manager.mark_failed(&item.id, &err_msg);
                errors.push(err_msg);
                failed += 1;
            }
        }
    }

    let remaining = queue_manager.get_count().unwrap_or(0);

    SyncResult {
        success: failed == 0,
        total_pending: total,
        synced_count: synced,
        failed_count: failed,
        remaining_pending: remaining,
        errors,
    }
}
