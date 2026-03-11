package com.clarity.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony

class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            for (message in messages) {
                val sender = message.originatingAddress ?: ""
                val body = message.messageBody ?: ""

                // Check if it's a UPI/bank SMS
                if (isUpiSms(body)) {
                    val serviceIntent = Intent(context, ClarityService::class.java)
                    serviceIntent.putExtra("sms_body", body)
                    context.startForegroundService(serviceIntent)
                }
            }
        }
    }

    private fun isUpiSms(body: String): Boolean {
        val lowerBody = body.lowercase()
        return (lowerBody.contains("debited") || lowerBody.contains("credited")) &&
                (lowerBody.contains("upi") || lowerBody.contains("rs.") || lowerBody.contains("inr"))
    }
}