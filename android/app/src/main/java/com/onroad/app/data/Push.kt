package com.onroad.app.data

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.onroad.app.MainActivity
import com.onroad.app.R
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import javax.inject.Inject

@Serializable data class PushTokenIn(val token: String, val platform: String = "android")

/** Price drops on saved cars and dealer quotes, pushed by the OnRoad server through Firebase Cloud Messaging. */
@AndroidEntryPoint
class PushService : FirebaseMessagingService() {
    @Inject lateinit var api: Api
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        scope.launch { runCatching { api.pushToken(PushTokenIn(token)) } }
    }

    override fun onMessageReceived(msg: RemoteMessage) {
        // in the background Android shows the notification itself; in the foreground we show it
        val n = msg.notification ?: return
        show(this, n.title ?: "OnRoad", n.body ?: "", msg.data["model"])
    }

    companion object {
        const val CHANNEL = "deals"

        fun channel(ctx: Context) {
            if (Build.VERSION.SDK_INT >= 26) ctx.getSystemService(NotificationManager::class.java)
                .createNotificationChannel(NotificationChannel(CHANNEL, "Price drops & dealer quotes", NotificationManager.IMPORTANCE_HIGH)
                    .apply { description = "Your saved cars getting cheaper, and dealers answering your quote requests" })
        }

        fun show(ctx: Context, title: String, body: String, model: String?) {
            channel(ctx)
            val open = PendingIntent.getActivity(ctx, title.hashCode(), Intent(ctx, MainActivity::class.java)
                .putExtra("open_model", model).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            runCatching {
                NotificationManagerCompat.from(ctx).notify(title.hashCode(), NotificationCompat.Builder(ctx, CHANNEL)
                    .setSmallIcon(R.drawable.ic_stat_notify).setContentTitle(title).setContentText(body)
                    .setStyle(NotificationCompat.BigTextStyle().bigText(body)).setContentIntent(open).setAutoCancel(true).build())
            }
        }

        /** Send this phone's token to the server (again after sign-in, so it is tied to the account). */
        fun register(api: Api, scope: CoroutineScope) {
            runCatching {
                FirebaseMessaging.getInstance().token.addOnSuccessListener { t -> scope.launch(Dispatchers.IO) { runCatching { api.pushToken(PushTokenIn(t)) } } }
            }
        }
    }
}
