// core/static/core/js/occurrence_autofill.js
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    var species  = document.getElementById('id_species');
    var checkbox = document.getElementById('id_is_rare');
    if (!species || !checkbox) return;

    function buildUrl(speciesId) {
      var base = window.location.pathname;                 // /admin/core/occurrence/add/
      base = base.replace(/(add\/|[0-9]+\/change\/)$/, ''); // -> /admin/core/occurrence/
      return base + 'species-rare-status/?species=' + encodeURIComponent(speciesId);
    }

    async function refreshFromServer() {
      var val = species.value;
      if (!val) return;                     // nimic selectat => nu modificăm
      try {
        const resp = await fetch(buildUrl(val), {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!resp.ok) return;
        const data = await resp.json();
        checkbox.checked = !!(data && data.is_rare);  // rămâne editabil manual
      } catch (e) {
        console.warn('rarity check failed', e);
      }
    }

    // 1) evenimentul nativ (în caz că nu e select2)
    species.addEventListener('change', refreshFromServer);

    // 2) evenimente Select2 în Admin
    var $ = (window.django && django.jQuery) || window.jQuery;
    if ($ && $(species).data('select2')) {
      $(species).on('select2:select select2:clear', function () {
        // mic delay ca Select2 să apuce să pună valoarea
        setTimeout(refreshFromServer, 0);
      });
    } else if ($) {
      // dacă select2 încă nu e inițializat, atașăm delegat (acoperă re-init)
      $(document).on('select2:select select2:clear', '#id_species', function () {
        setTimeout(refreshFromServer, 0);
      });
    }

    // 3) populați dacă există deja o specie selectată (ex. când reveniți pe pagină)
    if (species.value) refreshFromServer();
  });
})();
