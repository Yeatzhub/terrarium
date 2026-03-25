# Terrarium 🌿

A cozy mobile game where users build and grow tiny terrariums. Real-time plant growth, daily care tasks, collection mechanics, and social sharing.

## Tech Stack

- **Platform:** Android (Kotlin + Jetpack Compose)
- **Architecture:** MVVM with Repository pattern
- **Storage:** Room database (local)
- **Dependency Injection:** Hilt

## Project Structure

```
app/
├── data/
│   ├── model/          # Room entities (Terrarium, Plant, PlantType, Inventory, User)
│   ├── repository/     # Data access layer
│   └── database/       # Room DAOs and database setup
├── ui/
│   ├── home/           # Main terrarium view
│   ├── shop/           # Seed packets, jars shop
│   ├── inventory/      # Seeds and cuttings
│   ├── social/         # Friends and marketplace (Phase 2)
│   ├── theme/          # Material 3 theming
│   └── components/     # Shared UI components
├── viewmodel/          # MVVM ViewModels
├── util/               # Game config and utilities
└── di/                 # Hilt dependency injection modules
```

## Building

```bash
./gradlew assembleDebug
```

## Features (Phase 1)

- ✅ Android project structure with Kotlin + Jetpack Compose
- ✅ MVVM architecture with Repository pattern
- ✅ Room database entities (Terrarium, Plant, PlantType, Inventory, User)
- ✅ Basic UI shell with bottom navigation
- ✅ Main terrarium view (placeholder jar display)

## Upcoming Features

- Phase 2: Level system, shop, daily tasks, achievements
- Phase 3: Animations, sound effects, notifications
- Phase 4: Friend system, gifting, marketplace, cloud sync