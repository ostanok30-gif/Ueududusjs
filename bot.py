<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>OxatovAccount</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{background:#000;font-family:'Inter',sans-serif;color:#fff;overflow-x:hidden;}
        .bg{position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at 80% 20%,rgba(40,40,60,0.3) 0%,#000 70%);z-index:-1;}
        canvas{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
        .container{position:relative;z-index:2;padding:28px 20px 90px;max-width:480px;margin:0 auto;}
        .header{margin-bottom:32px;}
        .brand{font-size:10px;font-weight:600;letter-spacing:4px;color:rgba(255,255,255,0.35);margin-bottom:16px;text-transform:uppercase;}
        .page-title{font-size:34px;font-weight:700;letter-spacing:-1px;line-height:1.1;margin-bottom:8px;}
        .page-desc{font-size:13px;color:rgba(255,255,255,0.4);}
        .balance-card{background:rgba(255,255,255,0.02);backdrop-filter:blur(10px);border-radius:24px;padding:20px;margin-bottom:24px;border:1px solid rgba(255,255,255,0.05);}
        .balance-label{font-size:11px;font-weight:500;letter-spacing:1.5px;color:rgba(255,255,255,0.4);margin-bottom:8px;text-transform:uppercase;}
        .balance-value{font-size:44px;font-weight:700;letter-spacing:-1px;}
        .balance-unit{font-size:14px;font-weight:400;color:rgba(255,255,255,0.4);margin-left:6px;}
        .stats{display:flex;gap:10px;margin-bottom:28px;}
        .stat{flex:1;background:rgba(255,255,255,0.02);border-radius:16px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,0.04);}
        .stat-num{font-size:18px;font-weight:600;}
        .stat-label{font-size:10px;color:rgba(255,255,255,0.35);margin-top:4px;text-transform:uppercase;}
        .card{background:rgba(255,255,255,0.02);border-radius:18px;padding:16px 18px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.04);cursor:pointer;transition:all 0.2s;}
        .card:active{transform:scale(0.98);background:rgba(255,255,255,0.04);}
        .card-title{font-size:16px;font-weight:500;margin-bottom:8px;}
        .card-row{display:flex;justify-content:space-between;align-items:flex-end;}
        .card-price{font-size:20px;font-weight:600;}
        .card-meta{font-size:12px;color:rgba(255,255,255,0.35);}
        .account{background:rgba(255,255,255,0.02);border-radius:18px;padding:16px 18px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.04);}
        .account.sold{opacity:0.35;}
        .account-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;}
        .account-phone{font-size:14px;font-weight:500;font-family:monospace;}
        .account-tag{font-size:10px;padding:4px 10px;background:rgba(255,255,255,0.05);border-radius:20px;color:rgba(255,255,255,0.5);}
        .account-info{font-size:12px;color:rgba(255,255,255,0.35);margin-bottom:14px;}
        .account-price{font-size:22px;font-weight:600;margin-bottom:14px;}
        .btn{border:none;border-radius:40px;padding:10px 18px;font-size:13px;font-weight:500;cursor:pointer;transition:all 0.2s;width:100%;}
        .btn-primary{background:#fff;color:#000;}
        .btn-primary:active{transform:scale(0.97);background:#e8e8e8;}
        .btn-outline{background:transparent;border:1px solid rgba(255,255,255,0.15);color:rgba(255,255,255,0.8);}
        .btn-outline:active{background:rgba(255,255,255,0.05);transform:scale(0.97);}
        .back-btn{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.05);border:none;border-radius:30px;padding:7px 14px;font-size:12px;font-weight:500;color:rgba(255,255,255,0.6);cursor:pointer;margin-bottom:20px;}
        .back-btn:active{background:rgba(255,255,255,0.1);transform:scale(0.97);}
        .order-item{background:rgba(255,255,255,0.02);border-radius:18px;padding:16px 18px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.04);}
        .order-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;}
        .order-phone{font-size:15px;font-weight:500;}
        .order-badge{font-size:10px;padding:4px 10px;background:rgba(255,255,255,0.05);border-radius:20px;color:rgba(255,255,255,0.5);}
        .order-id{font-size:10px;color:rgba(255,255,255,0.3);font-family:monospace;margin-bottom:10px;}
        .code-block{font-size:28px;font-weight:700;font-family:monospace;letter-spacing:4px;text-align:center;padding:14px;background:rgba(0,0,0,0.4);border-radius:14px;margin:14px 0;cursor:pointer;}
        .code-block:active{background:rgba(255,255,255,0.05);}
        .news-item{background:rgba(255,255,255,0.02);border-radius:18px;padding:16px 18px;margin-bottom:10px;border-left:2px solid #fff;}
        .news-title{font-size:15px;font-weight:600;margin-bottom:6px;}
        .news-date{font-size:10px;color:rgba(255,255,255,0.3);margin-top:8px;}
        .tab-bar{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,0.96);backdrop-filter:blur(20px);padding:10px 20px;padding-bottom:calc(10px + env(safe-area-inset-bottom));display:flex;gap:8px;justify-content:space-around;border-top:1px solid rgba(255,255,255,0.05);z-index:10;}
        .tab{flex:1;text-align:center;padding:10px 6px;border-radius:12px;cursor:pointer;transition:all 0.2s;}
        .tab.active{background:rgba(255,255,255,0.06);}
        .tab-icon{font-size:12px;font-weight:500;letter-spacing:0.5px;margin-bottom:4px;color:rgba(255,255,255,0.4);text-transform:uppercase;}
        .tab.active .tab-icon{color:#fff;}
        .tab-label{font-size:9px;color:rgba(255,255,255,0.3);text-transform:uppercase;}
        .tab.active .tab-label{color:rgba(255,255,255,0.6);}
        .modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.95);backdrop-filter:blur(16px);display:flex;align-items:center;justify-content:center;z-index:1000;}
        .modal-content{background:#0c0c10;border-radius:28px;padding:32px 24px;max-width:300px;width:85%;text-align:center;border:1px solid rgba(255,255,255,0.06);}
        .modal-code{font-size:42px;font-weight:700;font-family:monospace;letter-spacing:6px;margin:20px 0;}
        .toast{position:fixed;bottom:90px;left:20px;right:20px;background:#1c1c22;border-radius:40px;padding:12px 20px;text-align:center;font-size:13px;z-index:100;border:1px solid rgba(255,255,255,0.06);}
        .loading{text-align:center;padding:60px 20px;}
        .spinner{width:32px;height:32px;border:2px solid rgba(255,255,255,0.08);border-top-color:#fff;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 16px;}
        @keyframes spin{to{transform:rotate(360deg);}}
        .empty{text-align:center;padding:60px 20px;color:rgba(255,255,255,0.3);font-size:13px;}
        .deposit-btn{margin-top:12px;}
    </style>
</head>
<body>
<div class="bg"></div>
<canvas id="starsCanvas"></canvas>
<div class="container" id="app"></div>
<div class="tab-bar">
    <div class="tab" data-tab="catalog"><div class="tab-icon">Каталог</div><div class="tab-label">Shop</div></div>
    <div class="tab" data-tab="orders"><div class="tab-icon">Заказы</div><div class="tab-label">Orders</div></div>
    <div class="tab" data-tab="news"><div class="tab-icon">Новости</div><div class="tab-label">News</div></div>
    <div class="tab" data-tab="profile"><div class="tab-icon">Профиль</div><div class="tab-label">Profile</div></div>
</div>
<script>
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();
    tg.enableClosingConfirmation();

    const canvas = document.getElementById('starsCanvas');
    const ctx = canvas.getContext('2d');
    let stars = [];
    let animFrame = null;

    function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
    function initStars() {
        stars = [];
        for (let i = 0; i < 160; i++) {
            stars.push({
                x: canvas.width * 0.8 + Math.random() * canvas.width * 0.3,
                y: Math.random() * canvas.height * 0.5,
                size: Math.random() * 2.5 + 0.8,
                speedX: -1.4 - Math.random() * 1.2,
                speedY: 0.5 + Math.random() * 0.9,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }
    function drawStars() {
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let s of stars) {
            s.x += s.speedX; s.y += s.speedY;
            if (s.x < -40 || s.y > canvas.height + 40) { s.x = canvas.width + 40; s.y = Math.random() * canvas.height * 0.4; }
            ctx.beginPath(); ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${s.opacity})`;
            ctx.fill();
        }
        animFrame = requestAnimationFrame(drawStars);
    }
    window.addEventListener('resize', () => { resizeCanvas(); initStars(); });
    resizeCanvas(); initStars(); drawStars();

    let currentTab = 'catalog';
    let balance = 0;
    let catalog = [];
    let orders = [];
    let codesMap = {};
    let selectedCountry = null;

    async function apiReq(url, opts = {}) {
        try { const res = await fetch(url, opts); return await res.json(); } catch(e) { return { error: true }; }
    }
    async function loadBalance() { const d = await apiReq('/api/balance'); balance = d.balance || 0; }
    async function loadCatalog() { const d = await apiReq('/api/catalog'); catalog = d.items || []; }
    async function loadOrders() { const d = await apiReq('/api/orders'); orders = d.orders || []; }
    async function loadCodes() { const d = await apiReq('/api/codes'); codesMap = {}; for (const c of d.codes || []) codesMap[c.order_id] = c; }
    async function refreshAll() { await Promise.all([loadBalance(), loadCatalog(), loadOrders(), loadCodes()]); }

    async function buyAccount(id, price) {
        if (balance < price) { toast(`Не хватает ${price} звезд`); return; }
        tg.showPopup({ title: 'Подтверждение', message: `Купить аккаунт за ${price} звезд?`, buttons: [{type:'ok',text:'Купить'},{type:'cancel',text:'Отмена'}] }, async (btn) => {
            if (btn !== 0) return;
            toast('Обработка...');
            const res = await apiReq('/api/buy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ account_id: id }) });
            if (res.success) { toast('Аккаунт куплен! Код в заказах'); await refreshAll(); render(); }
            else { toast('Аккаунт уже продан, деньги возвращены'); await refreshAll(); render(); }
        });
    }

    async function refreshCode(orderId, phone) {
        toast('Запрос нового кода...');
        const res = await apiReq('/api/refresh_code', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order_id: orderId, phone }) });
        if (res.success) { toast('Новый код отправлен'); await loadCodes(); render(); }
    }

    function toast(msg) {
        let t = document.getElementById('toast'); if (t) t.remove();
        t = document.createElement('div'); t.id = 'toast'; t.className = 'toast'; t.textContent = msg;
        document.body.appendChild(t); setTimeout(() => t.remove(), 2500);
    }

    function showCode(phone, code) {
        const modal = document.createElement('div'); modal.className = 'modal';
        modal.innerHTML = `<div class="modal-content"><div style="font-size:12px;color:rgba(255,255,255,0.5);">Код подтверждения</div><div class="modal-code">${code}</div><div style="font-size:11px;color:rgba(255,255,255,0.35);">Действителен 3 минуты</div><button class="btn-outline" style="margin-top:24px;width:100%;" onclick="this.closest('.modal').remove()">Закрыть</button></div>`;
        document.body.appendChild(modal);
    }

    async function depositStars() {
        tg.showPopup({
            title: 'Пополнение баланса', message: 'Выберите сумму в звездах:',
            buttons: [{type:'default',text:'50 ★'},{type:'default',text:'100 ★'},{type:'default',text:'200 ★'},{type:'cancel',text:'Отмена'}]
        }, async (btn) => {
            if (btn === 0) await apiReq('/api/deposit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: 50 }) });
            else if (btn === 1) await apiReq('/api/deposit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: 100 }) });
            else if (btn === 2) await apiReq('/api/deposit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: 200 }) });
            if (btn !== 3) toast('Инструкция по оплате отправлена в бота');
        });
    }

    function render() {
        if (currentTab === 'catalog') renderCatalog();
        else if (currentTab === 'orders') renderOrders();
        else if (currentTab === 'news') renderNews();
        else if (currentTab === 'profile') renderProfile();
        document.querySelectorAll('.tab').forEach(t => t.dataset.tab === currentTab ? t.classList.add('active') : t.classList.remove('active'));
    }

    function renderCatalog() {
        const root = document.getElementById('app');
        if (!catalog.length) { root.innerHTML = '<div class="loading"><div class="spinner"></div><div>Загрузка...</div></div>'; return; }
        const groups = {};
        for (const item of catalog) { if (!groups[item.country]) groups[item.country] = []; groups[item.country].push(item); }
        let html = `<div class="header"><div class="brand">OXATOV</div><div class="page-title">Магазин<br>аккаунтов</div><div class="page-desc">Telegram сессии</div></div>
        <div class="balance-card"><div class="balance-label">Баланс</div><div><span class="balance-value">${balance}</span><span class="balance-unit">звезд</span></div></div>
        <div class="stats"><div class="stat"><div class="stat-num">${catalog.length}</div><div class="stat-label">аккаунтов</div></div>
        <div class="stat"><div class="stat-num">${Object.keys(groups).length}</div><div class="stat-label">стран</div></div>
        <div class="stat"><div class="stat-num">${orders.length}</div><div class="stat-label">заказов</div></div></div>`;
        for (const [country, items] of Object.entries(groups)) {
            const minPrice = Math.min(...items.map(i => i.price));
            html += `<div class="card" onclick="selectCountry('${country}')"><div class="card-title">${country}</div><div class="card-row"><span class="card-price">от ${minPrice} ★</span><span class="card-meta">${items.length} шт</span></div></div>`;
        }
        root.innerHTML = html;
    }

    window.selectCountry = function(country) {
        selectedCountry = country;
        const items = catalog.filter(i => i.country === country);
        let html = `<button class="back-btn" onclick="backToCatalog()">← Назад</button>
        <div class="header"><div class="brand">${country.toUpperCase()}</div><div class="page-title">${country}</div><div class="page-desc">Telegram аккаунты</div></div>
        <div class="balance-card"><div class="balance-label">Ваш баланс</div><div><span class="balance-value">${balance}</span><span class="balance-unit">звезд</span></div></div>`;
        for (let i = 0; i < items.length; i++) {
            const a = items[i];
            const sold = a.status !== 'available';
            html += `<div class="account ${sold ? 'sold' : ''}"><div class="account-row"><span class="account-phone">${a.phone || '——'}</span><span class="account-tag">${a.dc || 'DC1'}</span></div>
            <div class="account-info">${country} · авторег</div><div class="account-price">${a.price} ★</div>
            ${!sold ? `<button class="btn-primary" onclick="buyAccount(${a.id}, ${a.price})">Купить</button>` : `<button class="btn-outline" disabled style="opacity:0.4">Продано</button>`}</div>`;
        }
        document.getElementById('app').innerHTML = html;
    };

    window.backToCatalog = function() { selectedCountry = null; renderCatalog(); };

    function renderOrders() {
        const root = document.getElementById('app');
        if (!orders.length) { root.innerHTML = `<div class="header"><div class="brand">ORDERS</div><div class="page-title">Заказы</div></div><div class="empty">У вас пока нет заказов</div>`; return; }
        let html = `<div class="header"><div class="brand">ORDERS</div><div class="page-title">Заказы</div></div>`;
        for (const order of orders) {
            const cd = codesMap[order.order_id];
            const hasCode = cd && new Date(cd.expires) > new Date();
            html += `<div class="order-item"><div class="order-header"><span class="order-phone">${order.phone}</span><span class="order-badge">${order.status === 'completed' ? 'выполнен' : 'ожидает'}</span></div>
            <div class="order-id">${order.order_id}</div><div style="margin-bottom:12px;">${order.amount} ★</div>
            ${hasCode ? `<div class="code-block" onclick="showCode('${order.phone}', '${cd.code}')">Показать код</div>
            <button class="btn-outline" style="width:100%;margin-top:8px;" onclick="refreshCode('${order.order_id}', '${order.phone}')">Запросить новый код</button>` :
            `<button class="btn-primary" onclick="refreshCode('${order.order_id}', '${order.phone}')">Запросить код</button>`}</div>`;
        }
        root.innerHTML = html;
    }

    function renderNews() {
        const news = [
            { title: "Аккаунты в наличии", text: "Telegram аккаунты доступны для покупки", date: "Июнь 2026" },
            { title: "Пополнение Stars", text: "Пополните баланс через Telegram Stars", date: "Июнь 2026" }
        ];
        let html = `<div class="header"><div class="brand">NEWS</div><div class="page-title">Новости</div></div>`;
        for (const item of news) {
            html += `<div class="news-item"><div class="news-title">${item.title}</div><div>${item.text}</div><div class="news-date">${item.date}</div></div>`;
        }
        root.innerHTML = html;
    }

    function renderProfile() {
        const user = tg.initDataUnsafe?.user || { id: '—', first_name: 'Пользователь' };
        const spent = orders.reduce((s, o) => s + o.amount, 0);
        const html = `<div class="header"><div class="brand">PROFILE</div><div class="page-title">${user.first_name}</div><div class="page-desc">${user.id}</div></div>
        <div class="stats"><div class="stat"><div class="stat-num">${balance}</div><div class="stat-label">баланс</div></div>
        <div class="stat"><div class="stat-num">${spent}</div><div class="stat-label">потрачено</div></div>
        <div class="stat"><div class="stat-num">${orders.length}</div><div class="stat-label">заказов</div></div></div>
        <button class="btn-primary deposit-btn" onclick="depositStars()">⭐ Пополнить баланс</button>
        <button class="btn-outline" style="margin-top:12px;" onclick="tg.openTelegramLink('https://t.me/oxatov')">Поддержка</button>`;
        document.getElementById('app').innerHTML = html;
    }

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            currentTab = tab.dataset.tab;
            if (selectedCountry && currentTab !== 'catalog') selectedCountry = null;
            render();
        });
    });

    refreshAll().then(() => render());
    setInterval(async () => { await refreshAll(); if (currentTab === 'catalog' && !selectedCountry) renderCatalog(); else if (currentTab === 'orders') renderOrders(); else if (currentTab === 'profile') renderProfile(); }, 15000);

    window.buyAccount = buyAccount;
    window.refreshCode = refreshCode;
    window.showCode = showCode;
    window.depositStars = depositStars;
</script>
</body>
</html>