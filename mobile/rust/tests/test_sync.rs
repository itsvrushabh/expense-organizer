use expense_sync_engine::queue::QueueManager;
use tempfile::NamedTempFile;

#[test]
fn test_enqueue_and_load() {
    let tmp = NamedTempFile::new().unwrap();
    let qm = QueueManager::new(tmp.path());

    let item = qm
        .enqueue("Groceries", 45.50, "Food", "2026-09-07")
        .unwrap();
    assert_eq!(item.description, "Groceries");
    assert_eq!(item.amount, 45.50);
    assert_eq!(item.category, "Food");
    assert_eq!(item.date, "2026-09-07");
    assert_eq!(item.status, "pending");

    let count = qm.get_count().unwrap();
    assert_eq!(count, 1);

    let items = qm.get_items().unwrap();
    assert_eq!(items.len(), 1);
    assert_eq!(items[0].id, item.id);
}

#[test]
fn test_mark_synced_and_clear() {
    let tmp = NamedTempFile::new().unwrap();
    let qm = QueueManager::new(tmp.path());

    let item1 = qm.enqueue("Milk", 3.50, "Food", "2026-09-07").unwrap();
    let _item2 = qm.enqueue("Gas", 30.00, "Transport", "2026-09-07").unwrap();

    assert_eq!(qm.get_count().unwrap(), 2);

    qm.mark_synced(&item1.id).unwrap();
    // Synced items don't count towards pending
    assert_eq!(qm.get_count().unwrap(), 1);

    let cleared = qm.clear_synced().unwrap();
    assert_eq!(cleared, 1);
    assert_eq!(qm.get_items().unwrap().len(), 1);
}

#[test]
fn test_mark_failed_retries() {
    let tmp = NamedTempFile::new().unwrap();
    let qm = QueueManager::new(tmp.path());

    let item = qm.enqueue("Coffee", 4.00, "Food", "2026-09-07").unwrap();
    qm.mark_failed(&item.id, "Connection refused").unwrap();

    let items = qm.get_items().unwrap();
    assert_eq!(items[0].status, "failed");
    assert_eq!(items[0].retry_count, 1);
    assert_eq!(items[0].last_error.as_deref(), Some("Connection refused"));
}
