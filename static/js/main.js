// Auto-dismiss messages after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const messages = document.querySelectorAll('.message');
  messages.forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(120%)';
      setTimeout(function () { msg.remove(); }, 400);
    }, 5000);
  });
});
