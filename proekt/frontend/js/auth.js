// Локально
// const API_URL = "http://127.0.0.1:8000";

// На продакшн
const API_URL = "https://prosvet-s4q3.onrender.com";

async function register(email, password) {
  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });

    const data = await res.json();

    if (!res.ok) {
      alert(`Ошибка регистрации: ${data.detail}`);
      return;
    }

    localStorage.removeItem("token");
    alert("Регистрация успешна! Перенаправление на страницу входа...");
    window.location.href = "login.html";
  } catch (error) {
    console.error("Ошибка подключения:", error);
    alert("Ошибка подключения к серверу");
  }
}

async function login(email, password) {
  try {
    localStorage.removeItem("token");

    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });

    const data = await res.json();

    if (!res.ok) {
      alert(`Ошибка входа: ${data.detail}`);
      return;
    }

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("email", email);

    // ✅ Синхронізувати папки з сервера
    await syncFolders(data.access_token);

    window.location.href = "notebook.html";
  } catch (error) {
    console.error("Ошибка подключения:", error);
    alert("Ошибка подключения к серверу");
  }
}

// ✅ Синхронізувати папки з сервера
async function syncFolders(token) {
  try {
    const res = await fetch(`${API_URL}/files/folders?token=${token}`);

    if (!res.ok) {
      console.error("Не удалось загрузить папки");
      return;
    }

    const folders = await res.json();
    console.log("📁 Синхронизированные папки:", folders);

    localStorage.setItem("folders", JSON.stringify(folders));
    return folders;
  } catch (error) {
    console.error("Ошибка синхронизации папок:", error);
  }
}

// ✅ Створити нову папку
async function createFolder() {
  const folderName = prompt("Введите имя папки:");

  if (!folderName || folderName.trim() === "") {
    alert("Имя папки не может быть пустым");
    return;
  }

  const token = localStorage.getItem("token");

  try {
    const formData = new FormData();
    formData.append("folder_name", folderName);

    const res = await fetch(`${API_URL}/files/create-folder?token=${token}`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      alert(`Ошибка: ${data.detail}`);
      return;
    }

    console.log("✅ Папка создана:", data);

    // Оновити список папок
    await syncFolders(token);
    displayFolders();

    alert(`Папка "${folderName}" создана!`);
  } catch (error) {
    console.error("Ошибка:", error);
    alert("Ошибка при создании папки");
  }
}

// ✅ Отримати папки
async function getFolders() {
  const token = localStorage.getItem("token");

  try {
    const res = await fetch(`${API_URL}/files/folders?token=${token}`);

    if (!res.ok) {
      return [];
    }

    return await res.json();
  } catch (error) {
    console.error("Ошибка:", error);
    return [];
  }
}

// ✅ Відобразити папки на сторінці
function displayFolders() {
  const foldersJSON = localStorage.getItem("folders");

  if (!foldersJSON) {
    console.log("Папка не найдена");
    return;
  }

  const folders = JSON.parse(foldersJSON);
  const folderList = document.getElementById("folder-list");

  if (!folderList) {
    console.log("Элемент #folder-list не найден");
    return;
  }

  folderList.innerHTML = "";

  folders.forEach((folder) => {
    const div = document.createElement("div");
    div.className = "folder-item";
    div.innerHTML = `
      <span onclick="goToFolder('${folder.id}')" style="cursor: pointer;">
        📁 ${folder.name}
      </span>
    `;
    folderList.appendChild(div);
  });
}

// ✅ Перейти в папку
function goToFolder(folderId) {
  window.location.href = `/folder/${folderId}`;
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("email");
  localStorage.removeItem("folders");
  window.location.href = "login.html";
}

// ✅ Ініціалізувати при завантаженні сторінки
async function initPage() {
  const token = localStorage.getItem("token");

  if (!token) {
    return;
  }

  // Завантажити папки з сервера
  const folders = await getFolders();
  console.log("📥 Загруженные папки:", folders);

  displayFolders();
}

window.addEventListener("load", initPage);
