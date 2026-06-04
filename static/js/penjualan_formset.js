// Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
// Form penjualan multi-row (formset) — tambah/hapus baris & stok picker.
// Data stok diinjeksi via #penjualanFormsetData JSON script tag.

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const el = document.getElementById('penjualanFormsetData');
    if (!el) return;
    const stockData = JSON.parse(el.textContent);

    const tbody          = document.getElementById('formset-body');
    const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
    const btnAdd         = document.getElementById('btn-add-row');

    const firstRow = tbody ? tbody.querySelector('.formset-row') : null;
    if (!firstRow) return;

    // Tombol "isi semua" — klik delegasi
    tbody.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-semua');
        if (!btn) return;
        const row         = btn.closest('.formset-row');
        const select      = row.querySelector('select[name$="-hasil_tangkap"]');
        const inputBerat  = row.querySelector('input[name$="-berat_terjual"]');
        if (select && inputBerat && select.value) {
            const tersedia = stockData[select.value];
            if (tersedia !== undefined) { inputBerat.value = tersedia; inputBerat.focus(); }
        }
    });

    // Update tooltip stok saat pilih hasil tangkap
    tbody.addEventListener('change', function (e) {
        if (!e.target.matches('select[name$="-hasil_tangkap"]')) return;
        const row  = e.target.closest('.formset-row');
        const btn  = row.querySelector('.btn-semua');
        const id   = e.target.value;
        if (id && stockData[id] !== undefined) {
            btn.title    = 'Stok tersedia: ' + stockData[id] + ' kg';
            btn.disabled = false;
        } else {
            btn.title    = 'Pilih hasil tangkap dulu';
            btn.disabled = true;
        }
    });

    // Tambah baris
    if (btnAdd) {
        btnAdd.addEventListener('click', function () {
            const total  = parseInt(totalFormsInput.value);
            const newRow = firstRow.cloneNode(true);
            newRow.querySelectorAll('input, select, textarea').forEach(function (el) {
                if (el.name) el.name = el.name.replace(/form-\d+-/, 'form-' + total + '-');
                if (el.id)   el.id   = el.id.replace(/id_form-\d+-/, 'id_form-' + total + '-');
                if (el.tagName === 'SELECT') el.selectedIndex = 0;
                else if (el.type === 'checkbox') el.checked = false;
                else el.value = '';
            });
            tbody.appendChild(newRow);
            totalFormsInput.value = total + 1;
            updateRemoveButtons();
        });
    }

    // Hapus baris — delegasi
    tbody.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-remove-row');
        if (!btn) return;
        const rows = tbody.querySelectorAll('.formset-row');
        if (rows.length <= 1) return;
        btn.closest('.formset-row').remove();
        const remaining = tbody.querySelectorAll('.formset-row');
        remaining.forEach(function (row, idx) {
            row.querySelectorAll('input, select, textarea').forEach(function (el) {
                if (el.name) el.name = el.name.replace(/form-\d+-/, 'form-' + idx + '-');
                if (el.id)   el.id   = el.id.replace(/id_form-\d+-/, 'id_form-' + idx + '-');
            });
        });
        totalFormsInput.value = remaining.length;
        updateRemoveButtons();
    });

    function updateRemoveButtons() {
        const rows = tbody.querySelectorAll('.formset-row');
        rows.forEach(function (row) {
            const btn = row.querySelector('.btn-remove-row');
            if (btn) btn.disabled = rows.length <= 1;
        });
    }
    updateRemoveButtons();
});
