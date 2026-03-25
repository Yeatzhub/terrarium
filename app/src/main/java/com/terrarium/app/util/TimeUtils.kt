package com.terrarium.app.util

import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.TimeUnit

/**
 * Utility object for time-related operations.
 */
object TimeUtils {
    private val dateFormat = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
    private val timeFormat = SimpleDateFormat("HH:mm", Locale.getDefault())
    
    fun formatTimestamp(timestamp: Long): String {
        val date = Date(timestamp)
        return "${dateFormat.format(date)} at ${timeFormat.format(date)}"
    }
    
    fun formatRelativeTime(timestamp: Long): String {
        val now = System.currentTimeMillis()
        val diff = now - timestamp
        
        return when {
            diff < TimeUnit.MINUTES.toMillis(1) -> "just now"
            diff < TimeUnit.HOURS.toMillis(1) -> {
                val minutes = TimeUnit.MILLISECONDS.toMinutes(diff)
                "$minutes minute${if (minutes != 1L) "s" else ""} ago"
            }
            diff < TimeUnit.DAYS.toMillis(1) -> {
                val hours = TimeUnit.MILLISECONDS.toHours(diff)
                "$hours hour${if (hours != 1L) "s" else ""} ago"
            }
            diff < TimeUnit.DAYS.toMillis(7) -> {
                val days = TimeUnit.MILLISECONDS.toDays(diff)
                "$days day${if (days != 1L) "s" else ""} ago"
            }
            else -> formatTimestamp(timestamp)
        }
    }
    
    fun hoursSince(timestamp: Long): Long {
        return TimeUnit.MILLISECONDS.toHours(System.currentTimeMillis() - timestamp)
    }
    
    fun daysSince(timestamp: Long): Long {
        return TimeUnit.MILLISECONDS.toDays(System.currentTimeMillis() - timestamp)
    }
}