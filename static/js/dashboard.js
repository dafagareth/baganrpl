// Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
// Dashboard analytics charts — data injected via #dashboardData JSON script tag.

(function () {
    'use strict';

    const el = document.getElementById('dashboardData');
    if (!el) return;
    const d = JSON.parse(el.textContent);

    const FONT   = { family: 'Google Sans Text, Roboto', size: 12 };
    const COLORS = ['#1E8E3E', '#1A73E8', '#E37400', '#D93025', '#9334E6', '#00796B'];

    // Warna mengikuti tema (terang/gelap) — ambil dari CSS variable supaya
    // teks sumbu, gridline, dan border donut tidak "putih" saat mode gelap.
    const css     = getComputedStyle(document.documentElement);
    const TEXT    = css.getPropertyValue('--ink-muted').trim()  || '#5F6368';
    const GRID    = css.getPropertyValue('--rule-soft').trim()  || '#E8EAED';
    const SURFACE = css.getPropertyValue('--surface').trim()    || '#fff';
    Chart.defaults.color = TEXT;

    function rpShort(v) {
        if (v >= 1e9) return 'Rp ' + (v / 1e9).toFixed(1) + ' M';
        if (v >= 1e6) return 'Rp ' + (v / 1e6).toFixed(1) + ' jt';
        if (v >= 1e3) return 'Rp ' + (v / 1e3).toFixed(0) + ' rb';
        return 'Rp ' + v;
    }

    // Chart 1 — Pendapatan vs Biaya
    new Chart(document.getElementById('chartRevenue'), {
        type: 'bar',
        data: {
            labels: d.labels,
            datasets: [
                { label: 'Pendapatan', data: d.pendapatan, backgroundColor: '#1E8E3E', borderRadius: 4, borderSkipped: false },
                { label: 'Biaya',      data: d.biaya,      backgroundColor: '#D93025', borderRadius: 4, borderSkipped: false },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { font: FONT, usePointStyle: true, padding: 16, boxWidth: 8 } },
                tooltip: { callbacks: { label: c => c.dataset.label + ': ' + rpShort(c.raw || 0) } },
            },
            scales: {
                x: { ticks: { font: FONT }, grid: { display: false } },
                y: { ticks: { font: FONT, callback: v => rpShort(v) }, grid: { color: GRID } },
            },
        },
    });

    // Chart 2 — Laba bersih
    new Chart(document.getElementById('chartLaba'), {
        type: 'bar',
        data: {
            labels: d.labels,
            datasets: [{
                label: 'Laba Bersih',
                data: d.laba,
                backgroundColor: d.laba.map(v => v >= 0 ? '#1E8E3E' : '#D93025'),
                borderRadius: 4, borderSkipped: false,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => 'Laba: ' + rpShort(Math.abs(c.raw)) + (c.raw < 0 ? ' (rugi)' : '') } },
            },
            scales: {
                x: { ticks: { font: FONT }, grid: { display: false } },
                y: { ticks: { font: FONT, callback: v => rpShort(v) }, grid: { color: GRID } },
            },
        },
    });

    // Chart 3 — Top tangkapan (horizontal)
    new Chart(document.getElementById('chartIkan'), {
        type: 'bar',
        data: {
            labels: d.ikanLabels,
            datasets: [{ label: 'kg', data: d.ikanData, backgroundColor: COLORS, borderRadius: 4 }],
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => (c.raw || 0).toFixed(1) + ' kg' } } },
            scales: {
                x: { ticks: { font: FONT, callback: v => v + ' kg' }, grid: { color: GRID } },
                y: { ticks: { font: FONT }, grid: { display: false } },
            },
        },
    });

    // Chart 4 — Top pembeli (horizontal)
    new Chart(document.getElementById('chartPembeli'), {
        type: 'bar',
        data: {
            labels: d.pembeliLabels,
            datasets: [{ label: 'Nilai', data: d.pembeliData, backgroundColor: COLORS.slice().reverse(), borderRadius: 4 }],
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => rpShort(c.raw || 0) } } },
            scales: {
                x: { ticks: { font: FONT, callback: v => rpShort(v) }, grid: { color: GRID } },
                y: { ticks: { font: FONT }, grid: { display: false } },
            },
        },
    });

    // Chart 5 — Biaya per bulan (garis)
    const biayaBulanCanvas = document.getElementById('chartBiayaBulan');
    if (biayaBulanCanvas) {
        new Chart(biayaBulanCanvas, {
            type: 'line',
            data: {
                labels: d.labels,
                datasets: [{
                    label: 'Biaya', data: d.biaya,
                    borderColor: '#D93025', backgroundColor: '#D93025',
                    tension: 0.3, fill: false, pointRadius: 3,
                }],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => rpShort(c.raw || 0) } } },
                scales: {
                    x: { ticks: { font: FONT }, grid: { display: false } },
                    y: { ticks: { font: FONT, callback: v => rpShort(v) }, grid: { color: GRID } },
                },
            },
        });
    }

    // Chart 6 — Utilisasi armada (horizontal) — hanya bila canvas ada (>1 kapal)
    const utilCanvas = document.getElementById('chartUtil');
    if (utilCanvas) {
        new Chart(utilCanvas, {
            type: 'bar',
            data: {
                labels: d.utilLabels,
                datasets: [{ label: 'Trip', data: d.utilData, backgroundColor: '#1A73E8', borderRadius: 4 }],
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => (c.raw || 0) + ' trip' } } },
                scales: {
                    x: { ticks: { font: FONT, stepSize: 1 }, grid: { color: GRID } },
                    y: { ticks: { font: FONT }, grid: { display: false } },
                },
            },
        });
    }
})();
