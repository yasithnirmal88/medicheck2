# Vercel Deployment Guide for Medicheck Frontend

## 📋 Pre-Deployment Checklist

### 1. Environment Variables Setup

Before deploying to Vercel, you must configure the following environment variables in your Vercel project settings.

#### Required Variables (VITE_ prefix required for Vite)

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `VITE_FIREBASE_API_KEY` | Firebase API Key | `AIzaSy...` |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase Auth Domain | `medicheck.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Firebase Project ID | `medicheck-app` |
| `VITE_API_BASE_URL` | Backend API URL | `https://api.medicheck.example.com/api/v1` |

#### How to Set Environment Variables in Vercel

1. **Via Vercel Dashboard:**
   - Navigate to your project
   - Go to **Settings** → **Environment Variables**
   - Add each variable with appropriate scope (Production, Preview, Development)

2. **Via Vercel CLI:**
   ```bash
   vercel env add VITE_FIREBASE_API_KEY
   vercel env add VITE_FIREBASE_AUTH_DOMAIN
   vercel env add VITE_FIREBASE_PROJECT_ID
   vercel env add VITE_API_BASE_URL
   ```

3. **Using Secrets (Recommended for production):**
   - In Vercel, prefix variable names with `@` to reference secrets
   - Example: `@firebase-api-key` references a stored secret

---

### 2. Firebase Configuration

#### Firebase Console Setup

1. **Create/Verify Firebase Project:**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Create or select your Medicheck project

2. **Enable Authentication:**
   - Navigate to **Authentication** → **Sign-in method**
   - Enable **Email/Password** provider
   - Enable **Google** provider (optional)

3. **Get Firebase Config:**
   - Go to **Project Settings** → **General**
   - Scroll to "Your apps" section
   - Copy the Firebase SDK configuration values

#### Required Firebase Services

- ✅ **Authentication** - Firebase Auth for user management
- ✅ **Firestore** (if using) - For real-time data
- ✅ **Hosting** (optional) - Can be managed via Vercel instead

---

### 3. Backend API Configuration

Ensure your backend API is accessible and CORS is configured for your Vercel domain.

#### CORS Configuration (Backend)

```python
# Add to your FastAPI backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://medicheck-frontend.vercel.app",  # Production
        "https://*.vercel.app",  # Preview deployments
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 Vercel Configuration

### vercel.json (Created)

```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.medicheck.example.com/api/v1/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

### Key Configuration Details

| Setting | Value | Notes |
|---------|-------|-------|
| **Framework** | `vite` | Vite/Vitest framework detection |
| **Build Command** | `npm run build` | Runs `vite build` |
| **Output Directory** | `dist` | Vite default output folder |
| **SPA Rewrites** | Enabled | All routes serve `index.html` |

---

## 📦 Build Configuration

### Vite Configuration (`vite.config.ts`)

The current Vite configuration is compatible with Vercel:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})
```

### Key Vite Settings for Vercel

| Setting | Current Value | Status |
|---------|---------------|--------|
| **Base URL** | `/` (default) | ✅ Compatible |
| **Output Directory** | `dist` | ✅ Matches vercel.json |
| **Build Target** | `esnext` | ✅ Modern browsers |
| **Path Aliases** | `@/*` | ✅ Works with Vercel |

---

## 🔒 Security Headers

The following security headers are configured in `vercel.json`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter (legacy) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer info |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Disables sensitive APIs |

---

## 🌐 Routing & SPA Configuration

### React Router Setup

The application uses `BrowserRouter` with 50+ routes:

| Route Pattern | Component | Auth Required |
|---------------|-----------|---------------|
| `/login` | LoginPage | No |
| `/app/*` | Dashboard | Yes |
| `/profile/*` | HealthProfilePage | Yes |
| `/questionnaires/*` | QuestionnaireListPage | Yes |
| `/assessments/*` | AssessmentSelectionPage | Yes |
| `/cms/*` | CMSLayout | Yes (Doctor) |
| `/*` | NotFound | No |

### SPA Rewrite Rules

All non-API routes are rewritten to `index.html` for client-side routing:

```json
{
  "rewrites": [
    {
      "source": "/((?!api/).*)",
      "destination": "/index.html"
    }
  ]
}
```

**Note:** The `framework: "vite"` setting in `vercel.json` automatically handles SPA routing. No manual rewrites needed for Vite projects.

---

## 🔗 API Integration

### Current API Configuration (`src/lib/api.ts`)

```typescript
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Firebase token attached automatically
api.interceptors.request.use(async (config) => {
  const auth = getAuth()
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | POST | Firebase token exchange |
| `/auth/register` | POST | User registration |
| `/auth/me` | GET | Current user profile |
| `/profiles/me/*` | GET/POST | Health profile CRUD |
| `/questionnaires/*` | GET/POST | Questionnaire operations |
| `/assessments/*` | GET | Assessment results |
| `/assessment/*` | GET/POST | CDSE operations |
| `/report/*` | GET/POST | Report generation |
| `/cms/*` | GET/POST/PUT/DELETE | CMS operations |

---

## 🚀 Deployment Steps

### Step 1: Prepare Repository

```bash
cd frontend

# Verify all dependencies
npm install

# Run typecheck
npm run typecheck

# Run lint
npm run lint

# Test build locally
npm run build
```

### Step 2: Connect to Vercel

**Option A: Via Dashboard**
1. Go to [vercel.com](https://vercel.com)
2. Import your Git repository
3. Select the `frontend` directory
4. Configure build settings

**Option B: Via CLI**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Step 3: Configure Environment Variables

1. In Vercel Dashboard → Project → Settings → Environment Variables
2. Add all required variables from `.env.example`
3. Set appropriate scopes (Production, Preview, Development)
4. Redeploy after adding variables

### Step 4: Configure Domain (Optional)

1. Project Settings → Domains
2. Add custom domain (e.g., `app.medicheck.com`)
3. Update DNS records as instructed
4. Wait for SSL certificate provisioning

### Step 5: Verify Deployment

1. Access preview/production URL
2. Test login flow
3. Verify API connectivity
4. Check browser console for errors

---

## 🧪 Testing Checklist

### Authentication Tests
- [ ] Login page loads correctly
- [ ] Firebase authentication works
- [ ] Protected routes redirect to login
- [ ] Logout clears session

### Navigation Tests
- [ ] Dashboard loads after login
- [ ] All sidebar links work
- [ ] Deep linking (refresh page) works
- [ ] 404 page displays correctly

### API Tests
- [ ] Profile data loads
- [ ] Questionnaires fetch successfully
- [ ] Assessments display results
- [ ] CMS pages load (doctor users)

### Performance Tests
- [ ] First Contentful Paint < 2s
- [ ] Time to Interactive < 3s
- [ ] Lighthouse score > 90

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Environment Variables Not Working

**Symptom:** `undefined` values for environment variables

**Solution:**
- Ensure variables start with `VITE_` prefix
- Redeploy after adding variables
- Check variable names match exactly

#### 2. CORS Errors

**Symptom:** `Access-Control-Allow-Origin` errors in console

**Solution:**
- Update backend CORS configuration
- Verify frontend URL is in allowed origins
- Check for protocol mismatch (http vs https)

#### 3. 404 on Page Refresh

**Symptom:** Direct URL access returns 404

**Solution:**
- Ensure `vercel.json` has correct configuration
- Verify `framework: "vite"` is set
- Check `outputDirectory: "dist"` is correct

#### 4. Firebase Auth Not Working

**Symptom:** Login fails or user is null

**Solution:**
- Verify Firebase config variables
- Check Firebase console for correct domain
- Ensure API key has proper restrictions

#### 5. API Requests Failing

**Symptom:** Network errors in console

**Solution:**
- Verify `VITE_API_BASE_URL` is correct
- Check backend is accessible
- Verify SSL certificate is valid

---

## 📞 Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel CLI Reference](https://vercel.com/docs/cli)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html)
- [Firebase Documentation](https://firebase.google.com/docs)

---

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-08-04 | 1.0.0 | Initial deployment guide |
