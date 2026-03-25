# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in Android SDK tools.
# For more details, see https://developer.android.com/build/shrink-code

# Keep Room entities
-keep class com.terrarium.app.data.model.** { *; }

# Keep DAO interfaces
-keep interface com.terrarium.app.data.database.** { *; }

# Kotlinx Coroutines
-keepclassmembers class kotlinx.coroutines.** {
    volatile <fields>;
}

# Gson
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.** { *; }