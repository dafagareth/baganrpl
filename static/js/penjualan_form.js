// Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
// Form penjualan tunggal — stok picker & tombol "isi semua".
// Data stok diinjeksi via #penjualanFormData JSON script tag.

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const el = document.getElementById('penjualanFormData');
    if (!el) return;
    const stockData = JSON.parse(el.textContent);

    const selectHasil = document.getElementById('id_hasil_tangkap');
    const inputBerat  = document.getElementById('id_berat_terjual');
    const btnSemua    = document.getElementById('btn-semua');
    const infoStok    = document.getElementById('info-stok');

    function updateStokInfo() {
        const id = selectHasil ? selectHasil.value : null;
        if (id && stockData[id] !== undefined) {
            infoStok.textContent = 'Stok tersedia: ' + stockData[id] + ' kg';
            btnSemua.disabled = false;
        } else {
            infoStok.textContent = '';
            btnSemua.disabled = true;
        }
    }

    if (selectHasil) { selectHasil.addEventListener('change', updateStokInfo); updateStokInfo(); }
    if (btnSemua) {
        btnSemua.addEventListener('click', function () {
            const id = selectHasil ? selectHasil.value : null;
            if (id && stockData[id] !== undefined) {
                inputBerat.value = stockData[id];
                inputBerat.focus();
            }
        });
    }
});
