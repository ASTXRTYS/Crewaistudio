# Manual Deployment Steps for Enhanced Dashboard

The enhanced dashboard has been built and uploaded to your server. You just need to complete these final steps:

## Quick Steps (Copy & Paste)

1. **SSH into your server:**
   ```bash
   ssh root@144.126.215.218
   ```
   Password: `.HvddX+@6dArsKd`

2. **Run these commands** (copy and paste each line):
   ```bash
   # Stop the system nginx that's blocking port 80
   systemctl stop nginx
   systemctl disable nginx
   
   # Go to the project directory
   cd /root/auren-production
   
   # Extract the enhanced dashboard
   tar -xzf /root/enhanced-dashboard.tar.gz -C auren/dashboard_v2/
   
   # Start Docker nginx
   docker-compose -f docker-compose.prod.yml up -d nginx
   
   # Verify it's working
   curl -s http://localhost | grep "index-CcacAJiZ.js" && echo "SUCCESS!" || echo "Still old version"
   ```

3. **Exit SSH:**
   ```bash
   exit
   ```

## Clear Your Browser Cache

**This is CRITICAL - your browser is caching the old version!**

### Mac:
- Chrome/Safari/Firefox: Press `Cmd + Shift + R`
- Or use Incognito mode: `Cmd + Shift + N`

### Windows:
- Chrome/Edge/Firefox: Press `Ctrl + Shift + R`
- Or use Incognito mode: `Ctrl + Shift + N`

## What You'll See

Once deployed and cache cleared, you'll see:

- 🌌 **Space-themed dark background** (deep gradient)
- 🔮 **Glassmorphic panels** with frosted glass blur effects
- ✨ **Glowing neon accents** (pink, blue, purple)
- 🎯 **Smooth animations** and transitions
- 🌟 **Enhanced visual effects** throughout

## Troubleshooting

If you still see the old dashboard:
1. Try a different browser
2. Use Private/Incognito mode
3. Clear all browser data for aupex.ai
4. Wait 2-3 minutes for any CDN cache to expire

The files ARE on the server - it's just a matter of nginx serving them and your browser loading the new version! 