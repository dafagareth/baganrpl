(function () {
  var modal = document.getElementById('addTangkapModal');
  if (!modal) return;

  function captureGPS() {
    var statusEl = document.getElementById('gps-status-wrap');
    var previewEl = document.getElementById('gps-preview');
    var latInput = document.getElementById('id_lat');
    var lngInput = document.getElementById('id_lng');

    if (!navigator.geolocation) {
      if (previewEl) previewEl.textContent = 'tidak didukung browser ini';
      return;
    }

    if (previewEl) previewEl.textContent = 'mengambil…';
    if (statusEl) statusEl.style.display = '';

    navigator.geolocation.getCurrentPosition(
      function (pos) {
        var lat = pos.coords.latitude.toFixed(6);
        var lng = pos.coords.longitude.toFixed(6);
        if (latInput) latInput.value = lat;
        if (lngInput) lngInput.value = lng;
        if (previewEl) previewEl.textContent = lat + ', ' + lng;
      },
      function () {
        if (previewEl) previewEl.textContent = 'tidak tersedia (izin ditolak)';
      },
      { timeout: 8000 }
    );
  }

  modal.addEventListener('show.bs.modal', captureGPS);
})();
