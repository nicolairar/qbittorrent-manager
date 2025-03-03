# qBittorrent Queue Manager 🚀 WORK IN PROGRESS... NOT WORKING AT ALL

qBittorrent Queue Manager is a Python script that automates the management of your torrent queue based on download speed. It monitors active torrents and moves slow torrents to the bottom of the queue after a defined period of slow speed. The script is designed to run inside a **Docker container**, making it easy to deploy and configure.

---

## 📦 Quick Install Using Portainer

Tired of managing slow torrents manually? No worries, let **qBittorrent Queue Manager** do the job for you! Here’s how you can set it up in **Portainer** in just a few clicks! 😃

### **1️⃣ Open Portainer and Navigate to "Stacks"**

1. Log in to **Portainer**.
2. In the left sidebar, click on **"Stacks"**.
3. Click on **"Add Stack"**.

### **2️⃣ Configure the Stack**

1. **Set a Name** for your stack (e.g., `qbit-manager`).
2. Select **"Git Repository"** as the build method.
3. In the **Repository URL** field, enter:
   ```
   https://github.com/nicolairar/qbittorrent-manager
   ```
4. In the **Repository Reference**, enter:
   ```
   refs/heads/main
   ```
5. In the **Compose Path**, enter:
   ```
   docker-compose.yml
   ```
6. (Optional) Enable **GitOps updates** if you want automatic updates!

### **3️⃣ Set Environment Variables 🛠️**

Portainer allows you to configure environment variables directly. Add these variables:

| Variable         | Value (Example)                    |
| ---------------- | ---------------------------------- |
| `QB_URL`         | `http://your-qbittorrent-url:8080` |
| `QB_USERNAME`    | `admin`                            |
| `QB_PASSWORD`    | `your_password`                    |
| `MIN_SPEED`      | `800` (Speed in KB/s)              |
| `CHECK_INTERVAL` | `180` (Time between checks in sec) |
| `LOG_PATH`       | `/var/log/qbit_queue_manager.log`  |

💡 **Pro Tip:** You can also upload a `.env` file with all variables pre-configured!

### **4️⃣ Deploy the Stack 🚀**

Once everything is set up:

1. Scroll down and click **"Deploy the Stack"**.
2. Wait for Portainer to pull the repository and start the container.
3. That’s it! Your qBittorrent manager is now running! 🎉

### **5️⃣ Verify Everything is Working ✅**

To check if everything is running smoothly:

```sh
docker logs -f qbit-manager
```

If you see logs with torrents being checked, you’re good to go! 😃

---

## 📝 License

This project is licensed under the **MIT License**. Feel free to use and modify it!

👨‍💻 **Contributions are welcome!** If you want to improve this project, feel free to submit a pull request! 💡

