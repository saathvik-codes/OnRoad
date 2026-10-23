# OnRoad 🚗🏍️

> **India's Transparent Automotive Intelligence & On-Road Price Discovery Platform**  
> Calculate exact state-by-state on-road prices, compare vehicle specs & official crash test safety, find verified authorized dealerships, and receive transparent showroom quotes.

[![Live Web Application](https://img.shields.io/badge/Live_App-onroad--frontend.onrender.com-success?style=for-the-badge&logo=render)](https://onroad-frontend.onrender.com)
[![FastAPI Backend](https://img.shields.io/badge/FastAPI_API-onroad--uu9c.onrender.com-blue?style=for-the-badge&logo=fastapi)](https://onroad-uu9c.onrender.com)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.4.2-black?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![SQLite WAL](https://img.shields.io/badge/SQLite-WAL_Persistent-003B57?style=for-the-badge&logo=sqlite)](https://sqlite.org)

---

## 🌟 Key Features

- **Itemised On-Road Price Breakdown**: Real-time tax calculator incorporating State Motor Vehicle Taxation Acts across all 36 States & Union Territories (Life-Time Tax, Central RTO, IRDAI Third-Party Insurance, TCS, and FASTag).
- **Interactive 3D Showroom Stage**: WebGL-powered 3D concept vehicle preview built with `@react-three/fiber` and `@react-three/drei`.
- **Catalogue & Technical Specifications**: Over 50 active brands, 500+ car & two-wheeler models, and 2,500+ variants complete with engine cc, transmission, fuel, battery capacity, and factory equipment.
- **Safety Intelligence**: Official Bharat NCAP and Global NCAP test scores, adult & child protection ratings, and tested airbag specifications.
- **Dealership Locator & Quotes Engine**: Browse over 2,200 verified authorized dealer showrooms across India with geocoded addresses, contact numbers, and transparent quotation requests.
- **Real-World Owner Reviews & Benchmarks**: Real-world mileage benchmarks and annual maintenance figures contributed by verified buyers.
- **Nightly Brand Scrapers**: Automated adapter ingestion engine syncing live ex-showroom pricelists, seasonal offers, and exchange bonuses directly from manufacturer portals.

---

## 🏗️ System Architecture

```
                       ┌───────────────────────────────┐
                       │      Browser / Mobile Web     │
                       └───────────────┬───────────────┘
                                       │
                      HTTPS :443 (Cloudflare Edge Proxy)
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │                                                     │
            ▼                                                     ▼
┌──────────────────────────────┐              ┌──────────────────────────────────────┐
│       Next.js Frontend       │              │           FastAPI Backend            │
│   (Port 3000 / Standalone)   │              │          (Port 8100 / Uvicorn)       │
│ • Server Components & SSR    │── rewrites ─▶│ • On-Road Tax Calculation Engine     │
│ • Three.js 3D Showcase       │  /api/:path* │ • Vehicle Specifications & Features  │
│ • Geocoded MapLibre Maps     │              │ • Live Dealer Ingestion Adapters     │
│ • Custom Brand Favicon Mark  │              │ • Cookie PBKDF2 Auth & User Sessions │
└──────────────────────────────┘              └──────────────────┬───────────────────┘
                                                                 │
                                                                 ▼
                                                  ┌──────────────────────────────┐
                                                  │       Persistent SQLite      │
                                                  │       (/data/onroad.db)      │
                                                  │ • Indexed for sub-millisecond│
                                                  │ • WAL mode concurrency       │
                                                  └──────────────────────────────┘
```

---

## 🚀 Live Services

| Service | Environment | Live URL | Description |
|---|---|---|---|
| **Web Frontend** | Render Web Service | [https://onroad-frontend.onrender.com](https://onroad-frontend.onrender.com) | Next.js 16 + React 19 UI |
| **Backend API** | Render Web Service | [https://onroad-uu9c.onrender.com](https://onroad-uu9c.onrender.com) | FastAPI + SQLite WAL with persistent volume |
| **API Documentation** | Swagger / OpenAPI | [https://onroad-uu9c.onrender.com/api/docs](https://onroad-uu9c.onrender.com/api/docs) | Interactive Swagger UI |

---

## 🛠️ Tech Stack

### Frontend (`/web`)
- **Framework**: Next.js 16 (App Router with Turbopack) & React 19
- **Styling**: Tailwind CSS v4, Lucide Icons
- **3D Visualization**: Three.js, React Three Fiber, React Three Drei
- **Maps**: MapLibre GL
- **Data Fetching**: SWR (Stale-While-Revalidate) & Lenis smooth scrolling

### Backend (`/backend`)
- **Engine**: FastAPI, Uvicorn (ASGI)
- **Database**: SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`)
- **Security**: PBKDF2 salted password hashing, HMAC signed session cookies
- **Ingestion**: Requests, BeautifulSoup4, HTTPX, Pillow image optimization

---

## 💻 Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/saathvik-codes/OnRoad.git
cd OnRoad
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Start FastAPI server on port 8100:
uvicorn onroad.api:app --reload --port 8100
```
API Documentation will be available at `http://127.0.0.1:8100/api/docs`.

### 3. Frontend Setup
In a new terminal window:
```bash
cd web
npm install --legacy-peer-deps

# Start Next.js dev server on port 3000:
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
```env
PORT=8100
API_SECRET=your_secure_random_hex_secret
COOKIE_SECURE=0               # Set to 1 in production (HTTPS)
DB_PATH=../data/onroad.db     # /data/onroad.db in production
IMG_CACHE=../data/img_cache
```

### Frontend (`web/.env.local`)
```env
PORT=3000
API_ORIGIN=http://127.0.0.1:8100   # Backend service URL
ALLOWED_DEV_ORIGINS=localhost,127.0.0.1
```

---

## 🚢 Production Deployment (Render.com)

This repository includes a pre-configured `render.yaml` Blueprint and Dockerfiles for one-click deployment:

1. Create a **New Blueprint Instance** on [Render.com](https://render.com).
2. Connect repository **`saathvik-codes/OnRoad`**.
3. Render automatically provisions:
   - `onroad-backend`: Docker container with a 1GB persistent disk mounted at `/data`.
   - `onroad-web`: Next.js Docker container running standalone production output.
4. Click **Apply** to launch both services.

---

## 📄 License
This project is proprietary and built for automotive price discovery in India. Vehicle names, logos, and trademarks belong to their respective manufacturers.
