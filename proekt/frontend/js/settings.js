const API_URL = "http://127.0.0.1:8000";

function qs(selector, root = document) {
  return root.querySelector(selector);
}

function saveSettingsToLocal(data) {
  localStorage.setItem("settings", JSON.stringify(data));
}

function loadSettingsFromLocal() {
  try {
    return JSON.parse(localStorage.getItem("settings")) || {};
  } catch {
    return {};
  }
}

function applyTheme(theme) {
  if (theme === "dark") document.body.classList.add("dark");
  else document.body.classList.remove("dark");
}

function setFieldsDisabled(disabled) {
  const fields = [
    qs("#firstName"),
    qs("#lastName"),
    qs("#emailField"),
    qs("#phoneField"),
    qs("#locationField"),
    qs("#aboutField"),
    qs("#avatarInput"),
  ];
  fields.forEach((f) => {
    if (f) f.disabled = disabled;
  });
}

function initSettings() {
  const settings = loadSettingsFromLocal();

  // Inputs
  const nameInput = qs("#firstName");
  const surnameInput = qs("#lastName");
  const emailInput = qs("#emailField");
  const phoneInput = qs("#phoneField");
  const locationInput = qs("#locationField");
  const aboutInput = qs("#aboutField");
  const avatarInput = qs("#avatarInput");
  const avatarPreview = qs("#avatarPreview");

  // Buttons
  const editProfileBtn = qs("#editProfileBtn");
  const profileActionButtons = qs("#profileActionButtons");
  const saveProfileBtn = qs("#saveProfileBtn");
  const cancelProfileBtn = qs("#cancelProfileBtn");
  const darkToggle = qs("#darkToggle");

  const currentPassword = qs("#currentPassword");
  const newPassword = qs("#newPassword");
  const confirmPassword = qs("#confirmPassword");
  const changePasswordBtn = qs("#changePasswordBtn");

  // Populate from localStorage
  if (settings.firstName) nameInput.value = settings.firstName;
  if (settings.lastName) surnameInput.value = settings.lastName;
  if (settings.email) emailInput.value = settings.email;
  if (settings.phone) phoneInput.value = settings.phone;
  if (settings.location) locationInput.value = settings.location;
  if (settings.about) aboutInput.value = settings.about;
  if (settings.avatarDataUrl)
    avatarPreview.style.backgroundImage = `url('${settings.avatarDataUrl}')`;

  // Initial state: all fields disabled
  setFieldsDisabled(true);

  // Theme
  const theme = localStorage.getItem("theme") || settings.theme || "light";
  darkToggle.checked = theme === "dark";
  applyTheme(theme);

  // Avatar preview
  avatarInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      alert("Выберите изображение");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      alert("Размер файла должен быть <= 2MB");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      avatarPreview.style.backgroundImage = `url('${reader.result}')`;
      const s = loadSettingsFromLocal();
      s.avatarDataUrl = reader.result;
      saveSettingsToLocal(s);
    };
    reader.readAsDataURL(file);
  });

  // Edit button: enable fields and show save/cancel buttons
  editProfileBtn.addEventListener("click", () => {
    setFieldsDisabled(false);
    editProfileBtn.classList.add("hidden");
    profileActionButtons.classList.remove("hidden");
  });

  // Cancel button: disable fields and hide save/cancel buttons (revert to initial values)
  cancelProfileBtn.addEventListener("click", () => {
    // Reload from localStorage
    if (settings.firstName) nameInput.value = settings.firstName;
    if (settings.lastName) surnameInput.value = settings.lastName;
    if (settings.email) emailInput.value = settings.email;
    if (settings.phone) phoneInput.value = settings.phone;
    if (settings.location) locationInput.value = settings.location;
    if (settings.about) aboutInput.value = settings.about;

    setFieldsDisabled(true);
    editProfileBtn.classList.remove("hidden");
    profileActionButtons.classList.add("hidden");
  });

  // Save profile
  saveProfileBtn.addEventListener("click", async () => {
    const data = {
      firstName: nameInput.value.trim(),
      lastName: surnameInput.value.trim(),
      email: emailInput.value.trim(),
      phone: phoneInput.value.trim(),
      location: locationInput.value.trim(),
      about: aboutInput.value.trim(),
      theme: darkToggle.checked ? "dark" : "light",
    };

    // Basic validation
    if (data.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(data.email)) {
      alert("Неверный формат email");
      return;
    }

    // Persist locally
    const prev = loadSettingsFromLocal();
    const merged = Object.assign({}, prev, data);
    saveSettingsToLocal(merged);
    localStorage.setItem("theme", merged.theme || "light");
    applyTheme(merged.theme);

    // Try to send to server if token present and endpoint exists
    const token = localStorage.getItem("token");
    if (token) {
      try {
        await fetch(`${API_URL}/users/update?token=${token}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
      } catch (e) {
        // ignore network errors — data already saved locally
      }
    }

    // Disable fields and revert buttons
    setFieldsDisabled(true);
    editProfileBtn.classList.remove("hidden");
    profileActionButtons.classList.add("hidden");

    alert("Профіль збережено");
  });

  // Theme toggle
  darkToggle.addEventListener("change", () => {
    const theme = darkToggle.checked ? "dark" : "light";
    localStorage.setItem("theme", theme);
    const s = loadSettingsFromLocal();
    s.theme = theme;
    saveSettingsToLocal(s);
    applyTheme(theme);
  });

  // Change password (client-side validation only)
  changePasswordBtn.addEventListener("click", async () => {
    if (
      !currentPassword.value ||
      !newPassword.value ||
      !confirmPassword.value
    ) {
      alert("Заполните все поля паролей");
      return;
    }
    if (newPassword.value.length < 6) {
      alert("Новый пароль должен содержать >= 6 символов");
      return;
    }
    if (newPassword.value !== confirmPassword.value) {
      alert("Пароли не совпадают");
      return;
    }

    // If backend supports password change endpoint, we can call it.
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Чтобы изменить пароль, пожалуйста, войдите");
      return;
    }

    try {
      const res = await fetch(
        `${API_URL}/auth/change-password?token=${token}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            current_password: currentPassword.value,
            new_password: newPassword.value,
          }),
        },
      );

      if (res.ok) {
        alert("Пароль изменен. Войдите с новым паролем.");
        // logout if function available
        if (typeof logout === "function") logout();
        else {
          localStorage.removeItem("token");
          window.location.href = "login.html";
        }
      } else {
        const d = await res
          .json()
          .catch(() => ({ detail: "Неизвестная ошибка" }));
        alert("Ошибка при смене пароля:" + (d.detail || ""));
      }
    } catch (e) {
      // Endpoint не існує — покажемо повідомлення і очистимо токен для безпеки
      alert(
        "Изменить пароль на сервере невозможно (нет endpoint). Локальные данные сохранены.",
      );
      localStorage.removeItem("token");
      window.location.href = "login.html";
    }
  });

  // Logout link handled by auth.js logout()
  const logoutLink = qs("#logoutLink");
  if (logoutLink)
    logoutLink.addEventListener("click", () => {
      if (typeof logout === "function") logout();
      else {
        localStorage.removeItem("token");
        window.location.href = "login.html";
      }
    });
}

window.addEventListener("load", initSettings);
