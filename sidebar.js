(function () {
  var body = document.body;
  var btn = document.getElementById('menu-btn');
  var overlay = document.getElementById('overlay');

  var saved = localStorage.getItem('sidebar');
  var prefersClosed = window.matchMedia('(max-width: 640px)').matches;
  body.dataset.sidebar = saved || (prefersClosed ? 'closed' : 'open');

  btn.addEventListener('click', function () {
    var next = body.dataset.sidebar === 'open' ? 'closed' : 'open';
    body.dataset.sidebar = next;
    localStorage.setItem('sidebar', next);
  });

  overlay.addEventListener('click', function () {
    body.dataset.sidebar = 'closed';
    localStorage.setItem('sidebar', 'closed');
  });
}());
