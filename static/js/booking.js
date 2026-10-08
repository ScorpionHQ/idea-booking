(function () {
  var container = document.getElementById("member-rows");
  var addBtn = document.getElementById("add-row");
  if (!container || !addBtn) return;

  var maxMembers = window.MAX_MEMBERS || 10;

  function currentCount() {
    return container.querySelectorAll(".member-row").length;
  }

  function updateCount() {
    var el = document.getElementById("member-count");
    if (el) el.textContent = currentCount();
  }

  function refreshButtons() {
    var rows = container.querySelectorAll(".member-row");
    var canRemove = rows.length > 1;
    rows.forEach(function (row) {
      var btn = row.querySelector(".remove-row");
      if (btn) btn.disabled = !canRemove;
    });
    addBtn.disabled = currentCount() + 1 >= maxMembers;
    updateCount();
  }

  addBtn.addEventListener("click", function () {
    if (currentCount() + 1 >= maxMembers) return;
    var row = document.createElement("div");
    row.className = "member-row";
    row.innerHTML =
      '<input type="text" name="member_name" placeholder="الاسم الكامل" required>' +
      '<input type="text" name="member_number" placeholder="الرقم الجامعي (اختياري)">' +
      '<button type="button" class="btn btn-danger btn-sm remove-row" title="حذف">✕</button>';
    container.appendChild(row);
    row.querySelector("input").focus();
    refreshButtons();
  });

  container.addEventListener("click", function (e) {
    if (!e.target.classList.contains("remove-row")) return;
    if (currentCount() <= 1) return;
    e.target.closest(".member-row").remove();
    refreshButtons();
  });

  refreshButtons();
})();
