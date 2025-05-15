// custom_admin.js
document.addEventListener("DOMContentLoaded", function () {
  // Пример: автоматический фокус на строку поиска
  const searchInput = document.querySelector('#searchbar input[type="text"]');
  if (searchInput) { searchInput.focus(); }
});