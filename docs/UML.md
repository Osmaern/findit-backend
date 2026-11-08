# UML diagrams: FindIt

The diagrams use Mermaid, which GitHub draws automatically when this file is viewed.

## 1. Use case diagram

```mermaid
flowchart LR
  visitor((Visitor))
  member((Member))
  mod((Moderator))
  sms[(Arkesel SMS)]

  visitor --> browse[Browse and search items]
  visitor --> view[View item page]
  visitor --> register[Register and verify phone]
  member --> report[Report lost or found item]
  member --> claim[Claim an item]
  member --> mine[Manage My Posts]
  member --> reportpost[Report a post]
  member --> profile[Edit profile and password]
  member --> reset[Reset forgotten password]
  mod --> queue[Review reports]
  mod --> remove[Remove or restore post]
  claim --> sms
  register --> sms
  reset --> sms
  remove --> sms
```

## 2. Class diagram (data model)

```mermaid
classDiagram
  class User {
    +int id
    +str full_name
    +str phone
    +str email
    +str role
    +bool phone_verified
    +int failed_logins
    +datetime locked_until
    +int token_version
  }
  class OTPCode {
    +int id
    +str purpose
    +str code_hash
    +int attempts
    +bool used
    +datetime expires_at
  }
  class Item {
    +int id
    +str kind
    +str title
    +str category
    +str location
    +date event_date
    +str status
    +bool allow_contact
    +datetime expires_at
  }
  class ItemPrivate {
    +str detail
  }
  class ItemPhoto {
    +int id
    +str file_name
    +str content_type
  }
  class Claim {
    +int id
    +str message
    +str status
  }
  class ItemReport {
    +int id
    +str reason
    +str status
  }
  User "1" --> "0..*" Item : posts
  Item "1" --> "0..1" ItemPrivate : private detail
  Item "1" --> "0..*" ItemPhoto : photos
  Item "1" --> "0..*" Claim : claims
  User "1" --> "0..*" Claim : makes
  Item "1" --> "0..*" ItemReport : reports
  User "1" --> "0..*" ItemReport : files
  User "1" --> "0..*" OTPCode : receives
```

## 3. State diagram (item status)

```mermaid
stateDiagram-v2
  [*] --> open : reported
  open --> claim_pending : claim approved
  open --> closed : owner closes
  open --> removed : moderator removes
  open --> expired : 60 days pass
  claim_pending --> returned : owner marks returned
  removed --> open : moderator restores
  returned --> [*]
  closed --> [*]
  expired --> [*]
```

## 4. Sequence diagram: claim and approval

```mermaid
sequenceDiagram
  actor C as Claimant
  actor O as Owner
  participant API as FindIt API
  participant DB as Database
  participant SMS as Arkesel

  C->>API: POST /items/{id}/claims (message)
  API->>DB: check item open, not own, no earlier claim
  API->>DB: save claim (pending)
  API-->>SMS: text owner "someone claimed your item"
  API-->>C: 201 claim pending
  O->>API: POST /claims/{id}/approve
  API->>DB: claim approved, item claim_pending, other claims declined
  API-->>SMS: text claimant "approved"
  API-->>SMS: text other claimants "not successful"
  API-->>O: 200 with claimant phone
  C->>API: GET /claims/mine
  API-->>C: owner phone (only if allow_contact)
```

## 5. Sequence diagram: password reset

```mermaid
sequenceDiagram
  actor U as Person
  participant API as FindIt API
  participant DB as Database
  participant SMS as Arkesel

  U->>API: POST /forgot-password (phone)
  API-->>U: same reply for every number
  opt verified account, not asked in last 60 s
    API->>DB: save code hash (purpose reset)
    API-->>SMS: text 6-digit code
  end
  U->>API: POST /reset-password (phone, code, new password)
  API->>DB: check code, expiry, attempts
  API->>DB: set password, token_version + 1, unlock account
  API-->>SMS: text "password changed"
  API-->>U: 200
```
