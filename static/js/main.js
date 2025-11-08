if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/static/js/sw.js');
}
function urlBase64ToUint8Array(base64String){
  const padding='='.repeat((4-base64String.length%4)%4);
  const base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');
  const rawData=atob(base64);
  return Uint8Array.from([...rawData].map(c=>c.charCodeAt(0)));
}

document.addEventListener('DOMContentLoaded',()=>{
  const btn=document.getElementById('enablePush');
  if(btn){
    btn.addEventListener('click', async ()=>{
      const perm=await Notification.requestPermission();
      if(perm!=='granted') return alert('الإشعارات غير مفعلة');
      const reg=await navigator.serviceWorker.ready;
      const sub=await reg.pushManager.subscribe({
        userVisibleOnly:true,
        applicationServerKey:urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });
      await fetch('/subscribe',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(sub)
      });
      alert('تم تفعيل الإشعارات ✅');
    });
  }
});