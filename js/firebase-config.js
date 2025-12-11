// ═══════════════════════════════════════════════════════════════
// BEE LIFE CONSULTING - FIREBASE CONFIGURATION
// Real-time Database for Applications, Sales, and Employee Data
// ═══════════════════════════════════════════════════════════════

// Firebase Configuration - Gerçek değerler (11 Aralık 2024)
const firebaseConfig = {
    apiKey: "AIzaSyApKLAGxHMM4cRZ8JRMFCMiWWaCbCmJi20",
    authDomain: "bee-life-consulting.firebaseapp.com",
    databaseURL: "https://bee-life-consulting-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "bee-life-consulting",
    storageBucket: "bee-life-consulting.firebasestorage.app",
    messagingSenderId: "367033938264",
    appId: "1:367033938264:web:a112a90db36c9ddfbeb52d",
    measurementId: "G-9PJD1VJVW6"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// ═══════════════════════════════════════════════════════════════
// DATABASE REFERENCES
// ═══════════════════════════════════════════════════════════════
const DB = {
    applications: database.ref('applications'),
    employees: database.ref('employees'),
    sales: database.ref('sales'),
    notifications: database.ref('notifications'),
    stats: database.ref('stats')
};

// ═══════════════════════════════════════════════════════════════
// APPLICATION FUNCTIONS (Başvuru İşlemleri)
// ═══════════════════════════════════════════════════════════════

// Yeni başvuru kaydet
async function saveApplication(applicationData) {
    try {
        const newRef = DB.applications.push();
        const appData = {
            ...applicationData,
            id: newRef.key,
            status: 'pending',
            createdAt: firebase.database.ServerValue.TIMESTAMP,
            appliedDate: new Date().toISOString()
        };
        await newRef.set(appData);
        console.log('✅ Başvuru kaydedildi:', newRef.key);
        return { success: true, id: newRef.key };
    } catch (error) {
        console.error('❌ Başvuru kaydetme hatası:', error);
        return { success: false, error: error.message };
    }
}

// Tüm başvuruları getir (Admin için)
function listenToApplications(callback) {
    DB.applications.orderByChild('createdAt').on('value', (snapshot) => {
        const applications = [];
        snapshot.forEach((child) => {
            applications.unshift({ id: child.key, ...child.val() });
        });
        callback(applications);
    });
}

// Başvuru durumunu güncelle
async function updateApplicationStatus(appId, status, notes = '') {
    try {
        await DB.applications.child(appId).update({
            status: status,
            notes: notes,
            updatedAt: firebase.database.ServerValue.TIMESTAMP
        });
        return { success: true };
    } catch (error) {
        console.error('❌ Durum güncelleme hatası:', error);
        return { success: false, error: error.message };
    }
}

// Başvuru sil
async function deleteApplication(appId) {
    try {
        await DB.applications.child(appId).remove();
        return { success: true };
    } catch (error) {
        console.error('❌ Silme hatası:', error);
        return { success: false, error: error.message };
    }
}

// ═══════════════════════════════════════════════════════════════
// EMPLOYEE FUNCTIONS (Personel İşlemleri)
// ═══════════════════════════════════════════════════════════════

// Personel verilerini kaydet/güncelle
async function saveEmployeeData(employeeId, data) {
    try {
        await DB.employees.child(employeeId).update({
            ...data,
            updatedAt: firebase.database.ServerValue.TIMESTAMP
        });
        return { success: true };
    } catch (error) {
        console.error('❌ Personel kaydetme hatası:', error);
        return { success: false, error: error.message };
    }
}

// Personel verilerini dinle (Real-time)
function listenToEmployee(employeeId, callback) {
    DB.employees.child(employeeId).on('value', (snapshot) => {
        callback(snapshot.val());
    });
}

// Tüm personelleri getir (Admin için)
function listenToAllEmployees(callback) {
    DB.employees.on('value', (snapshot) => {
        const employees = [];
        snapshot.forEach((child) => {
            employees.push({ id: child.key, ...child.val() });
        });
        callback(employees);
    });
}

// ═══════════════════════════════════════════════════════════════
// SALES FUNCTIONS (Satış İşlemleri)
// ═══════════════════════════════════════════════════════════════

// Satış kaydet
async function saveSale(employeeId, saleData) {
    try {
        const newRef = DB.sales.push();
        await newRef.set({
            ...saleData,
            id: newRef.key,
            employeeId: employeeId,
            createdAt: firebase.database.ServerValue.TIMESTAMP,
            date: new Date().toISOString()
        });
        
        // Personel istatistiklerini güncelle
        await updateEmployeeStats(employeeId, saleData);
        
        return { success: true, id: newRef.key };
    } catch (error) {
        console.error('❌ Satış kaydetme hatası:', error);
        return { success: false, error: error.message };
    }
}

// Personel istatistiklerini güncelle
async function updateEmployeeStats(employeeId, saleData) {
    const statsRef = DB.employees.child(employeeId).child('stats');
    
    try {
        const snapshot = await statsRef.once('value');
        const currentStats = snapshot.val() || {
            totalSales: 0,
            qcOk: 0,
            wr: 0,
            rls: 0,
            callCount: 0,
            workHours: 0,
            commission: 0
        };
        
        // İstatistikleri güncelle
        const newStats = {
            totalSales: currentStats.totalSales + (saleData.sales || 0),
            qcOk: currentStats.qcOk + (saleData.qcOk || 0),
            wr: currentStats.wr + (saleData.wr || 0),
            rls: currentStats.rls + (saleData.rls || 0),
            callCount: currentStats.callCount + (saleData.callCount || 0),
            workHours: currentStats.workHours + (saleData.workHours || 0),
            commission: currentStats.commission + (saleData.commission || 0),
            lastUpdated: firebase.database.ServerValue.TIMESTAMP
        };
        
        await statsRef.set(newStats);
        return { success: true };
    } catch (error) {
        console.error('❌ İstatistik güncelleme hatası:', error);
        return { success: false, error: error.message };
    }
}

// Personel satışlarını dinle
function listenToEmployeeSales(employeeId, callback) {
    DB.sales.orderByChild('employeeId').equalTo(employeeId).on('value', (snapshot) => {
        const sales = [];
        snapshot.forEach((child) => {
            sales.unshift({ id: child.key, ...child.val() });
        });
        callback(sales);
    });
}

// Tüm satışları dinle (Admin için)
function listenToAllSales(callback) {
    DB.sales.orderByChild('createdAt').on('value', (snapshot) => {
        const sales = [];
        snapshot.forEach((child) => {
            sales.unshift({ id: child.key, ...child.val() });
        });
        callback(sales);
    });
}

// ═══════════════════════════════════════════════════════════════
// NOTIFICATION FUNCTIONS (Bildirim İşlemleri)
// ═══════════════════════════════════════════════════════════════

// Bildirim gönder
async function sendNotification(notificationData) {
    try {
        const newRef = DB.notifications.push();
        await newRef.set({
            ...notificationData,
            id: newRef.key,
            createdAt: firebase.database.ServerValue.TIMESTAMP,
            date: new Date().toISOString()
        });
        return { success: true, id: newRef.key };
    } catch (error) {
        console.error('❌ Bildirim gönderme hatası:', error);
        return { success: false, error: error.message };
    }
}

// Bildirimleri dinle
function listenToNotifications(callback) {
    DB.notifications.orderByChild('createdAt').limitToLast(50).on('value', (snapshot) => {
        const notifications = [];
        snapshot.forEach((child) => {
            notifications.unshift({ id: child.key, ...child.val() });
        });
        callback(notifications);
    });
}

// Bildirim sil
async function deleteNotification(notificationId) {
    try {
        await DB.notifications.child(notificationId).remove();
        return { success: true };
    } catch (error) {
        console.error('❌ Bildirim silme hatası:', error);
        return { success: false, error: error.message };
    }
}

// ═══════════════════════════════════════════════════════════════
// GLOBAL STATS FUNCTIONS (Genel İstatistikler)
// ═══════════════════════════════════════════════════════════════

// Genel istatistikleri güncelle
async function updateGlobalStats(statsData) {
    try {
        await DB.stats.update({
            ...statsData,
            lastUpdated: firebase.database.ServerValue.TIMESTAMP
        });
        return { success: true };
    } catch (error) {
        console.error('❌ Global stats hatası:', error);
        return { success: false, error: error.message };
    }
}

// Genel istatistikleri dinle
function listenToGlobalStats(callback) {
    DB.stats.on('value', (snapshot) => {
        callback(snapshot.val() || {});
    });
}

// ═══════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════

// Bağlantı durumunu kontrol et
function checkConnection(callback) {
    const connectedRef = database.ref('.info/connected');
    connectedRef.on('value', (snap) => {
        callback(snap.val() === true);
    });
}

// Listener'ları temizle
function cleanup() {
    DB.applications.off();
    DB.employees.off();
    DB.sales.off();
    DB.notifications.off();
    DB.stats.off();
}

// Export for global use
window.BeeLifeDB = {
    // Applications
    saveApplication,
    listenToApplications,
    updateApplicationStatus,
    deleteApplication,
    
    // Employees
    saveEmployeeData,
    listenToEmployee,
    listenToAllEmployees,
    
    // Sales
    saveSale,
    updateEmployeeStats,
    listenToEmployeeSales,
    listenToAllSales,
    
    // Notifications
    sendNotification,
    listenToNotifications,
    deleteNotification,
    
    // Stats
    updateGlobalStats,
    listenToGlobalStats,
    
    // Utilities
    checkConnection,
    cleanup
};

console.log('🐝 Bee Life Firebase initialized');

