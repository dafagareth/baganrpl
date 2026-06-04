// Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
// Public landing page interactive chart — data via #publicChartData JSON script tag.

(function () {
    'use strict';

    const el = document.getElementById('publicChartData');
    if (!el) return;
    const d = JSON.parse(el.textContent);

    const BRAND = '#1A73E8';
    const RED   = '#D93025';
    const GREEN = '#34A853';
    const FONT  = { family: 'Google Sans Text, Roboto, sans-serif' };

    function isDark() {
        const t = document.documentElement.getAttribute('data-theme');
        if (t === 'dark')  return true;
        if (t === 'light') return false;
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    function rpFmt(v) {
        if (Math.abs(v) >= 1e9) return 'Rp ' + (v / 1e9).toFixed(1) + ' M';
        if (Math.abs(v) >= 1e6) return 'Rp ' + (v / 1e6).toFixed(1) + ' jt';
        if (Math.abs(v) >= 1e3) return 'Rp ' + (v / 1e3).toFixed(0) + ' rb';
        return 'Rp ' + v;
    }

    const datasets = {
        revenue: {
            datasets: [
                { label: 'Pendapatan', data: d.pendapatan, borderColor: BRAND, backgroundColor: 'rgba(26,115,232,.08)', borderWidth: 2, fill: true, tension: .3, pointBackgroundColor: BRAND, pointBorderColor: '#fff', pointBorderWidth: 2, pointRadius: 4 },
                { label: 'Biaya',      data: d.biaya,      borderColor: RED,   backgroundColor: 'transparent', borderWidth: 1.5, borderDash: [5, 4], fill: false, tension: .3, pointBackgroundColor: RED, pointBorderColor: '#fff', pointBorderWidth: 1.5, pointRadius: 3 },
            ],
        },
        laba: {
            datasets: [
                { label: 'Laba Bersih', data: d.laba, borderColor: GREEN, backgroundColor: 'rgba(46,125,50,.08)', borderWidth: 2, fill: true, tension: .3, pointBackgroundColor: GREEN, pointBorderColor: '#fff', pointBorderWidth: 2, pointRadius: 4 },
            ],
        },
        tangkap: {
            datasets: [
                { label: 'Volume Tangkap (kg)', data: d.tangkap, borderColor: '#E65100', backgroundColor: 'rgba(230,81,0,.07)', borderWidth: 2, fill: true, tension: .3, pointBackgroundColor: '#E65100', pointBorderColor: '#fff', pointBorderWidth: 2, pointRadius: 4 },
            ],
        },
    };

    const ctx = document.getElementById('publicChart').getContext('2d');
    let chart;

    function buildChart(type) {
        if (chart) chart.destroy();
        const MUTED = isDark() ? '#9AA0A6' : '#5F6368';
        const GRID  = isDark() ? '#3C4043' : '#E8EAED';
        chart = new Chart(ctx, {
            type: 'line',
            data: { labels: d.labels, ...datasets[type] },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: { position: 'bottom', labels: { color: MUTED, font: FONT, usePointStyle: true, padding: 16, boxWidth: 8 } },
                    tooltip: {
                        backgroundColor: '#202124',
                        titleFont: { ...FONT, size: 13 }, bodyFont: { ...FONT, size: 12 },
                        padding: 10, cornerRadius: 4, displayColors: true,
                        callbacks: {
                            label: c => {
                                const v = c.raw || 0;
                                return ' ' + c.dataset.label + ': ' + (type === 'tangkap' ? v.toLocaleString('id-ID') + ' kg' : rpFmt(v));
                            },
                        },
                    },
                },
                scales: {
                    x: { ticks: { color: MUTED, font: { ...FONT, size: 11 } }, grid: { display: false } },
                    y: {
                        ticks: {
                            color: MUTED, font: { ...FONT, size: 11 },
                            callback: v => type === 'tangkap' ? (v >= 1000 ? (v / 1000).toFixed(1) + ' ton' : v + ' kg') : rpFmt(v),
                        },
                        grid: { color: GRID },
                    },
                },
            },
        });
    }

    buildChart('revenue');

    document.querySelectorAll('.chart-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chart-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            buildChart(btn.dataset.chart);
        });
    });

    // Dipanggil saat tema diubah — perbarui warna chart
    window.__refreshChartTheme = function () {
        const active = document.querySelector('.chart-tab.active');
        buildChart(active ? active.dataset.chart : 'revenue');
    };
})();
