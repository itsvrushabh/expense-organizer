use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_double, c_int};
use crate::queue::QueueManager;
use crate::sync::{check_online, sync_pending_queue};

unsafe fn c_to_str<'a>(ptr: *const c_char) -> Result<&'a str, String> {
    if ptr.is_null() {
        return Err("Null pointer passed".to_string());
    }
    CStr::from_ptr(ptr)
        .to_str()
        .map_err(|e| format!("Invalid UTF-8: {e}"))
}

fn to_c_string(s: String) -> *mut c_char {
    CString::new(s).unwrap_or_default().into_raw()
}

#[no_mangle]
pub unsafe extern "C" fn rust_free_string(s: *mut c_char) {
    if !s.is_null() {
        drop(CString::from_raw(s));
    }
}

#[no_mangle]
pub unsafe extern "C" fn rust_check_server_online(
    api_url: *const c_char,
    timeout_ms: u32,
) -> c_int {
    let url = match c_to_str(api_url) {
        Ok(u) => u,
        Err(_) => return 0,
    };

    if check_online(url, timeout_ms as u64) {
        1
    } else {
        0
    }
}

#[no_mangle]
pub unsafe extern "C" fn rust_enqueue_expense(
    queue_path: *const c_char,
    description: *const c_char,
    amount: c_double,
    category: *const c_char,
    date_str: *const c_char,
) -> *mut c_char {
    let path = match c_to_str(queue_path) {
        Ok(p) => p,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };
    let desc = match c_to_str(description) {
        Ok(d) => d,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };
    let cat = match c_to_str(category) {
        Ok(c) => c,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };
    let date = match c_to_str(date_str) {
        Ok(d) => d,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };

    let qm = QueueManager::new(path);
    match qm.enqueue(desc, amount, cat, date) {
        Ok(item) => to_c_string(serde_json::to_string(&item).unwrap_or_default()),
        Err(e) => to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    }
}

#[no_mangle]
pub unsafe extern "C" fn rust_get_queue(queue_path: *const c_char) -> *mut c_char {
    let path = match c_to_str(queue_path) {
        Ok(p) => p,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };

    let qm = QueueManager::new(path);
    match qm.get_items() {
        Ok(items) => to_c_string(serde_json::to_string(&items).unwrap_or_else(|_| "[]".to_string())),
        Err(e) => to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    }
}

#[no_mangle]
pub unsafe extern "C" fn rust_get_pending_queue(queue_path: *const c_char) -> *mut c_char {
    let path = match c_to_str(queue_path) {
        Ok(p) => p,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };

    let qm = QueueManager::new(path);
    match qm.get_pending_items() {
        Ok(items) => to_c_string(serde_json::to_string(&items).unwrap_or_else(|_| "[]".to_string())),
        Err(e) => to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    }
}

#[no_mangle]
pub unsafe extern "C" fn rust_get_queue_count(queue_path: *const c_char) -> c_int {
    let path = match c_to_str(queue_path) {
        Ok(p) => p,
        Err(_) => return -1,
    };

    let qm = QueueManager::new(path);
    match qm.get_count() {
        Ok(c) => c as c_int,
        Err(_) => -1,
    }
}

#[no_mangle]
pub unsafe extern "C" fn rust_sync_queue(
    queue_path: *const c_char,
    api_url: *const c_char,
) -> *mut c_char {
    let path = match c_to_str(queue_path) {
        Ok(p) => p,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };
    let url = match c_to_str(api_url) {
        Ok(u) => u,
        Err(e) => return to_c_string(format!(r#"{{"error":"{e}"}}"#)),
    };

    let qm = QueueManager::new(path);
    let result = sync_pending_queue(&qm, url);
    to_c_string(serde_json::to_string(&result).unwrap_or_default())
}

#[no_mangle]
pub unsafe extern "C" fn rust_clear_synced(queue_path: *const c_char) -> c_int {
    let path = match c_to_str(queue_path) {
        Ok(p) => p,
        Err(_) => return -1,
    };

    let qm = QueueManager::new(path);
    match qm.clear_synced() {
        Ok(c) => c as c_int,
        Err(_) => -1,
    }
}
