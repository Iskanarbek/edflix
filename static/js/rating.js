function initRating(rateUrl, csrfToken) {
  const container = document.querySelector('.star-rating');
  if (!container) return;

  const stars = container.querySelectorAll('.star');
  let currentRating = parseInt(container.dataset.current || '0');

  function setDisplay(val) {
    stars.forEach(function (s, i) {
      if (i < val) {
        s.classList.add('star-filled');
      } else {
        s.classList.remove('star-filled');
      }
    });
  }

  stars.forEach(function (star) {
    star.addEventListener('mouseenter', function () {
      setDisplay(parseInt(this.dataset.value));
    });
    star.addEventListener('mouseleave', function () {
      setDisplay(currentRating);
    });
    star.addEventListener('click', function () {
      const val = parseInt(this.dataset.value);
      const formData = new FormData();
      formData.append('rating', val);
      formData.append('csrfmiddlewaretoken', csrfToken);

      fetch(rateUrl, { method: 'POST', body: formData })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            currentRating = val;
            setDisplay(currentRating);
            const avgEl = document.getElementById('avgRating');
            if (avgEl) avgEl.textContent = data.avg_rating;
          }
        })
        .catch(function () {});
    });
  });

  setDisplay(currentRating);
}
