// Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
// Tambah/hapus baris generik untuk Django modelformset (prefix default "form").
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        var tbody  = document.getElementById('formset-body');
        var total  = document.getElementById('id_form-TOTAL_FORMS');
        var btnAdd = document.getElementById('btn-add-row');
        if (!tbody || !total || !btnAdd) return;

        function reindex(row, idx) {
            row.querySelectorAll('input, select, textarea').forEach(function (el) {
                if (el.name) el.name = el.name.replace(/form-\d+-/, 'form-' + idx + '-');
                if (el.id)   el.id   = el.id.replace(/form-\d+-/, 'form-' + idx + '-');
            });
            row.querySelectorAll('.text-danger').forEach(function (e) { e.remove(); });
        }

        btnAdd.addEventListener('click', function () {
            var rows = tbody.querySelectorAll('.formset-row');
            var clone = rows[rows.length - 1].cloneNode(true);
            var idx = parseInt(total.value, 10);
            reindex(clone, idx);
            clone.querySelectorAll('input, select, textarea').forEach(function (el) {
                if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
                else el.value = '';
            });
            tbody.appendChild(clone);
            total.value = idx + 1;
        });

        tbody.addEventListener('click', function (e) {
            var btn = e.target.closest('.btn-remove-row');
            if (!btn) return;
            var rows = tbody.querySelectorAll('.formset-row');
            if (rows.length <= 1) return;            // sisakan minimal satu baris
            btn.closest('.formset-row').remove();
            tbody.querySelectorAll('.formset-row').forEach(function (row, i) { reindex(row, i); });
            total.value = tbody.querySelectorAll('.formset-row').length;
        });
    });
})();
