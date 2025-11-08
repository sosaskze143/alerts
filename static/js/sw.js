self.addEventListener('push', e=>{
  let data=e.data?e.data.json():{};
  const title=data.title||'تنبيه جديد';
  const options={
    body:data.body||'',
    icon:'/static/images/logo2.png',
    badge:'/static/images/logo2.png',
    image:data.image||undefined
  };
  e.waitUntil(self.registration.showNotification(title,options));
});
self.addEventListener('notificationclick', e=>{
  e.notification.close();
  e.waitUntil(clients.openWindow('/'));
});