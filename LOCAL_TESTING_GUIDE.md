# Local Testing Guide for Production Cookie Fixes

## Why Test Locally?

The JWT cookie issue only occurs in production (Render) due to:
- HTTPS requirements
- Proxy/load balancer interference  
- Cross-site cookie restrictions
- Browser security policies

## Testing Setup

### 1. Start Flask with Production Settings

```bash
# Option 1: Use the simulation script
python simulate_production.py

# Option 2: Manual setup
export FLASK_ENV=production
export FLASK_DEBUG=0
export JWT_COOKIE_SECURE=True
export JWT_COOKIE_SAMESITE=Lax
python -m flask run --host=0.0.0.0 --port=5000 --no-debugger --no-reload
```

### 2. Run the Cookie Test

```bash
python test_production_cookies.py
```

### 3. Manual Browser Testing

1. **Start your React frontend** (if separate):
   ```bash
   cd frontend
   npm start
   ```

2. **Open browser** and go to `http://localhost:3000`

3. **Test login flow** and check browser developer tools:
   - Network tab: Check cookie headers
   - Application tab: Check stored cookies
   - Console: Look for JWT errors

## What to Look For

### ✅ Success Indicators
- Login succeeds (200 response)
- `/api/me` returns user data (200 response)
- FCM token saving works (200 response)
- No "Token expired" errors in logs
- New cookies are set and used

### ❌ Failure Indicators  
- Login succeeds but `/api/me` fails (401)
- "Token expired" errors in logs
- Old expired tokens still being used
- Cookie clearing not working

## Debugging Tips

### 1. Check Cookie Headers
```bash
# Use curl to test API endpoints
curl -v -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ray40","password":"Raysan11!!","lot_number":"test","pass_token":"test","captcha_output":"test"}' \
  -c cookies.txt

curl -v -X GET http://localhost:5000/api/me \
  -b cookies.txt
```

### 2. Monitor Flask Logs
Look for these debug messages:
- `[DEBUG] Response cookies:`
- `[DEBUG] Set-Cookie headers:`
- `[ME DEBUG] Request cookies:`
- `[JWT DEBUG] Token expired:`

### 3. Browser Developer Tools
- **Network tab**: Check if cookies are sent with requests
- **Application tab**: Verify cookie storage and clearing
- **Console**: Look for authentication errors

## Expected Results

If the fixes work locally, you should see:

1. **Cookie clearing works**: Old cookies are properly deleted
2. **New cookies are set**: Fresh JWT tokens are created
3. **Authentication flows**: `/api/me` and FCM endpoints work
4. **No token conflicts**: Only new tokens are used

## Next Steps

If local testing passes:
1. ✅ **Deploy to Render**
2. ✅ **Test in production**
3. ✅ **Verify FCM works**

If local testing fails:
1. 🔧 **Debug the specific issue**
2. 🔧 **Adjust the fix**
3. 🔧 **Test again locally**

## Troubleshooting

### Common Issues

**Issue**: Cookies not being cleared
**Solution**: Check if `clear-cookies` endpoint is working

**Issue**: New cookies not being set
**Solution**: Verify JWT configuration in `app.py`

**Issue**: Old tokens still being used
**Solution**: Check browser cache and try incognito mode

**Issue**: CORS errors
**Solution**: Verify `ALLOWED_ORIGINS` includes localhost 