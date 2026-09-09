use std::fs::{self, File};
use std::io::{BufReader, BufWriter};
use std::path::{Path, PathBuf};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct QueueItem {
    pub id: String,
    pub description: String,
    pub amount: f64,
    pub category: String,
    pub date: String,
    pub status: String, // "pending", "synced", "failed"
    pub retry_count: u32,
    pub created_at: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_error: Option<String>,
}

#[derive(Debug, Clone)]
pub struct QueueManager {
    file_path: PathBuf,
}

impl QueueManager {
    pub fn new<P: AsRef<Path>>(file_path: P) -> Self {
        Self {
            file_path: file_path.as_ref().to_path_buf(),
        }
    }

    pub fn load(&self) -> Result<Vec<QueueItem>, String> {
        if !self.file_path.exists() {
            return Ok(Vec::new());
        }

        let file = File::open(&self.file_path).map_err(|e| format!("Failed to open queue file: {e}"))?;
        let reader = BufReader::new(file);
        let items: Vec<QueueItem> = serde_json::from_reader(reader).unwrap_or_else(|_| Vec::new());
        Ok(items)
    }

    pub fn save(&self, items: &[QueueItem]) -> Result<(), String> {
        if let Some(parent) = self.file_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent).map_err(|e| format!("Failed to create queue dir: {e}"))?;
            }
        }

        let file = File::create(&self.file_path).map_err(|e| format!("Failed to create queue file: {e}"))?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, items).map_err(|e| format!("Failed to serialize queue: {e}"))?;
        Ok(())
    }

    pub fn enqueue(
        &self,
        description: &str,
        amount: f64,
        category: &str,
        date: &str,
    ) -> Result<QueueItem, String> {
        let mut items = self.load()?;

        let item = QueueItem {
            id: Uuid::new_v4().to_string(),
            description: description.trim().to_string(),
            amount,
            category: category.trim().to_string(),
            date: date.trim().to_string(),
            status: "pending".to_string(),
            retry_count: 0,
            created_at: Utc::now().to_rfc3339(),
            last_error: None,
        };

        items.push(item.clone());
        self.save(&items)?;
        Ok(item)
    }

    pub fn get_items(&self) -> Result<Vec<QueueItem>, String> {
        self.load()
    }

    pub fn get_pending_items(&self) -> Result<Vec<QueueItem>, String> {
        let items = self.load()?;
        Ok(items
            .into_iter()
            .filter(|item| item.status == "pending" || item.status == "failed")
            .collect())
    }

    pub fn get_count(&self) -> Result<usize, String> {
        let items = self.get_pending_items()?;
        Ok(items.len())
    }

    pub fn mark_synced(&self, id: &str) -> Result<(), String> {
        let mut items = self.load()?;
        for item in &mut items {
            if item.id == id {
                item.status = "synced".to_string();
                item.last_error = None;
                break;
            }
        }
        self.save(&items)
    }

    pub fn mark_failed(&self, id: &str, error: &str) -> Result<(), String> {
        let mut items = self.load()?;
        for item in &mut items {
            if item.id == id {
                item.status = "failed".to_string();
                item.retry_count += 1;
                item.last_error = Some(error.to_string());
                break;
            }
        }
        self.save(&items)
    }

    pub fn remove(&self, id: &str) -> Result<bool, String> {
        let mut items = self.load()?;
        let initial_len = items.len();
        items.retain(|item| item.id != id);
        let removed = items.len() < initial_len;
        if removed {
            self.save(&items)?;
        }
        Ok(removed)
    }

    pub fn clear_synced(&self) -> Result<usize, String> {
        let mut items = self.load()?;
        let initial_len = items.len();
        items.retain(|item| item.status != "synced");
        let removed = initial_len - items.len();
        if removed > 0 {
            self.save(&items)?;
        }
        Ok(removed)
    }
}
