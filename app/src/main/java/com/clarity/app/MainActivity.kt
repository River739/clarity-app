package com.clarity.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private val client = OkHttpClient()
    private val scope = CoroutineScope(Dispatchers.IO)
    private val BASE_URL = "http://10.0.2.2:8000"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        requestSmsPermission()

        val emailInput = findViewById<EditText>(R.id.emailInput)
        val passwordInput = findViewById<EditText>(R.id.passwordInput)
        val loginButton = findViewById<Button>(R.id.loginButton)
        val statusText = findViewById<TextView>(R.id.statusText)

        val prefs = getSharedPreferences("clarity_prefs", MODE_PRIVATE)
        val token = prefs.getString("auth_token", "")
        if (!token.isNullOrEmpty()) {
            statusText.text = "✅ Clarity is active and monitoring transactions"
            loginButton.text = "Logout"
            loginButton.setOnClickListener {
                prefs.edit().remove("auth_token").apply()
                statusText.text = "Logged out"
                loginButton.text = "Login"
            }
            return
        }

        loginButton.setOnClickListener {
            val email = emailInput.text.toString()
            val password = passwordInput.text.toString()

            if (email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Enter email and password", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            statusText.text = "Logging in..."

            scope.launch {
                try {
                    val formBody = "username=${email}&password=${password}"
                    val body = formBody.toRequestBody("application/x-www-form-urlencoded".toMediaType())

                    val request = Request.Builder()
                        .url("$BASE_URL/login")
                        .post(body)
                        .build()

                    val response = client.newCall(request).execute()
                    val responseBody = response.body?.string() ?: ""

                    if (response.isSuccessful) {
                        val json = JSONObject(responseBody)
                        val token = json.getString("access_token")
                        val name = json.getString("name")

                        prefs.edit().putString("auth_token", token).apply()

                        withContext(Dispatchers.Main) {
                            statusText.text = "✅ Welcome $name! Clarity is now monitoring your transactions."
                            loginButton.text = "Logout"
                        }
                    } else {
                        withContext(Dispatchers.Main) {
                            statusText.text = "❌ Login failed. Check your credentials."
                        }
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        statusText.text = "❌ Error: ${e.message}"
                    }
                }
            }
        }
    }

    private fun requestSmsPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECEIVE_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECEIVE_SMS, Manifest.permission.READ_SMS),
                100
            )
        }
    }
}