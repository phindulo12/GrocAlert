# 🛒 GrocAlert – Smart Grocery Tracker

**GrocAlert** is a smart grocery tracking web application designed to help users manage their food inventory, avoid waste, and save money. It offers features like barcode scanning, expiry alerts, profile-based grocery duration estimation, and local store price comparisons in South Africa.

---

## 🚀 Features

- 📦 **Barcode Scanning** – Quickly add items using barcodes (via OpenFoodFacts API).
- ⏰ **Expiry Tracking** – Get alerts for items nearing expiry.
- 👤 **User Profiles** – Personalized experience with age/gender-based consumption estimates.
- 🧮 **Grocery Duration Estimator** – Estimates how long groceries will last using Nutritionix/USDA data.
- 🛍 **Local Price Comparison** – Find best prices from South African stores (via iGrosa or other APIs).
- 📸 **Profile Picture Upload** – Upload and edit profile avatars.
- 🔐 **Secure Authentication** – Register/login system using Flask-Login.

---

## 🧱 Built With

- **Python** & **Flask**
- **SQLite**
- **Bootstrap 5**
- **JavaScript**
- **OpenFoodFacts API**, **Nutritionix API**, **iGrosa API**
- **Flask-Login**, **Flask-WTF**, **Flask-Migrate**

---

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/grocalert.git
cd grocalert
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
flask run
```

---

## 📁 Project Structure

```
/grocalert
│
├── static/
├── templates/
├── .render/           # Deployment scripts
├── app.py             # Main Flask app
├── models.py          # Database models
├── forms.py           # WTForms
├── utils/             # Utility functions
└── requirements.txt
```

--
## 📸 Screenshots

> Add screenshots of the profile dashboard, barcode scan feature, and alerts screen.

---

## 🌐 Deployment

This app is ready for deployment on **Render** with `build.sh` and `start` commands configured.


## 👨‍💻 Author

**Phindulo** – [github](https://github.com/phindulo12)  
Feel free to contribute, suggest features, or report bugs!
