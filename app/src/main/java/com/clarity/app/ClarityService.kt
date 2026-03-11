package com.clarity.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class ClarityService : Service() {

    private val client = OkHttpClient()
    private val scope = CoroutineScope(Dispatchers.IO)
    private val BASE_URL = "http://10.0.2.2:8000" // 10.0.2.2 = localhost for Android emulator

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        startForeground(1, buildNotification())

        val smsBody = intent?.getStringExtra("sms_body") ?: return START_NOT_STICKY

        scope.launch {
            sendSmsToBackend(smsBody)
        }

        return START_NOT_STICKY
    }

    private fun sendSmsToBackend(smsBody: String) {
        try {
            // Get token from SharedPreferences
            val prefs = getSharedPreferences("clarity_prefs", MODE_PRIVATE)
            val token = prefs.getString("auth_token", "") ?: ""

            if (token.isEmpty()) return

            val json = JSONObject()
            json.put("text", smsBody)

            val body = json.toString().toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url("$BASE_URL/parse-sms")
                .addHeader("Authorization", "Bearer $token")
                .post(body)
                .build()

            client.newCall(request).execute()

        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            "clarity_channel",
            "Clarity Finance",
            NotificationManager.IMPORTANCE_LOW
        )
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    private fun buildNotification(): Notification {
        return Notification.Builder(this, "clarity_channel")
            .setContentTitle("Clarity")
            .setContentText("Monitoring transactions...")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}