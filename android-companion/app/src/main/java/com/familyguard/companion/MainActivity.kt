package com.familyguard.companion

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.UUID
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {
    private val preferences by lazy { getSharedPreferences("companion", MODE_PRIVATE) }
    private val companionId by lazy {
        preferences.getString("companion_id", null) ?: UUID.randomUUID().toString().also {
            preferences.edit().putString("companion_id", it).apply()
        }
    }
    private lateinit var serverUrl: EditText
    private lateinit var pairingCode: EditText
    private lateinit var consent: CheckBox
    private lateinit var connectionStatus: TextView
    private val permissionRequest = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        val granted = results.values.count { it }
        Toast.makeText(this, "$granted permission(s) granted by Android", Toast.LENGTH_SHORT).show()
    }

    private val screenRequest = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        Toast.makeText(this, if (result.resultCode == RESULT_OK) "Screen sharing allowed" else "Screen sharing declined", Toast.LENGTH_SHORT).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        serverUrl = findViewById(R.id.serverUrl)
        pairingCode = findViewById(R.id.pairingCode)
        consent = findViewById(R.id.consent)
        connectionStatus = findViewById(R.id.connectionStatus)
        findViewById<Button>(R.id.enroll).setOnClickListener { enroll() }
        findViewById<Button>(R.id.notifications).setOnClickListener {
            if (consent.isChecked) requestIfNeeded(arrayOf(Manifest.permission.POST_NOTIFICATIONS)) else requireConsent()
        }
        findViewById<Button>(R.id.sms).setOnClickListener {
            if (consent.isChecked) requestIfNeeded(arrayOf(Manifest.permission.READ_SMS, Manifest.permission.RECEIVE_SMS)) else requireConsent()
        }
        findViewById<Button>(R.id.calls).setOnClickListener {
            if (consent.isChecked) requestIfNeeded(arrayOf(Manifest.permission.READ_CALL_LOG, Manifest.permission.READ_PHONE_STATE)) else requireConsent()
        }
        findViewById<Button>(R.id.usage).setOnClickListener {
            if (consent.isChecked) startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)) else requireConsent()
        }
        findViewById<Button>(R.id.screen).setOnClickListener {
            if (!consent.isChecked) {
                requireConsent()
                return@setOnClickListener
            }
            val manager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            screenRequest.launch(manager.createScreenCaptureIntent())
        }
        preferences.getString("token", null)?.let { connectionStatus.text = "Connected to Render. Token saved on this phone." }
    }

    private fun enroll() {
        if (!consent.isChecked) {
            requireConsent()
            return
        }
        val base = serverUrl.text.toString().trim().trimEnd('/')
        val code = pairingCode.text.toString().trim().uppercase()
        if (base.isBlank() || code.isBlank()) {
            connectionStatus.text = "Enter the Render URL and pairing code."
            return
        }
        connectionStatus.text = "Connecting..."
        thread {
            try {
                val response = postForm("$base/api/companion/enroll/", mapOf("pairing_code" to code, "companion_id" to companionId))
                if (response.first !in 200..299) throw IllegalStateException(response.second)
                val token = JSONObject(response.second).getString("token")
                preferences.edit().putString("server", base).putString("token", token).apply()
                runOnUiThread { connectionStatus.text = "Connected. Permission status will sync to Render." }
                heartbeat(base, token)
            } catch (error: Exception) {
                runOnUiThread { connectionStatus.text = "Connection failed: ${error.message ?: "check code and consent"}" }
            }
        }
    }

    private fun heartbeat(base: String, token: String) {
        val permissions = JSONObject()
            .put("notifications", ContextCompat.checkSelfPermission(this, "android.permission.POST_NOTIFICATIONS") == PackageManager.PERMISSION_GRANTED)
            .put("sms", ContextCompat.checkSelfPermission(this, "android.permission.READ_SMS") == PackageManager.PERMISSION_GRANTED)
            .put("call_log", ContextCompat.checkSelfPermission(this, "android.permission.READ_CALL_LOG") == PackageManager.PERMISSION_GRANTED)
            .put("phone_state", ContextCompat.checkSelfPermission(this, "android.permission.READ_PHONE_STATE") == PackageManager.PERMISSION_GRANTED)
            .put("screen_share", false)
        thread {
            try {
                postForm("$base/api/companion/$token/heartbeat/", mapOf("companion_id" to companionId, "permissions" to permissions.toString()))
            } catch (_: Exception) {
                runOnUiThread { connectionStatus.text = "Offline. The app will retry when opened." }
            }
        }
    }

    private fun postForm(endpoint: String, values: Map<String, String>): Pair<Int, String> {
        val connection = (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 15000
            readTimeout = 15000
            setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
        }
        val body = values.entries.joinToString("&") { "${URLEncoder.encode(it.key, "UTF-8")}=${URLEncoder.encode(it.value, "UTF-8")}" }
        connection.outputStream.use { it.write(body.toByteArray()) }
        val status = connection.responseCode
        val stream = if (status in 200..299) connection.inputStream else connection.errorStream
        return status to (stream?.bufferedReader()?.use { it.readText() } ?: "")
    }

    private fun requestIfNeeded(permissions: Array<String>) {
        val missing = permissions.filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
        if (missing.isNotEmpty()) permissionRequest.launch(missing.toTypedArray())
        else Toast.makeText(this, "Already allowed in Android settings", Toast.LENGTH_SHORT).show()
    }

    private fun requireConsent() {
        Toast.makeText(this, "Review and accept the consent checkbox first", Toast.LENGTH_LONG).show()
    }
}