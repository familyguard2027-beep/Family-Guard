package com.familyguard.companion

import android.Manifest
import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.CheckBox
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
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

        val consent = findViewById<CheckBox>(R.id.consent)
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