setInterval(() => {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            // 可在此更新 dashboard 的卡片，但简单起见留空
        });
}, 60000);
