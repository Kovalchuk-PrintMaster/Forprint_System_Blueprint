# Warehouse Service — evening delta

A separate Warehouse capability may be justified if it owns physical stock truth.

Possible canonical data:
- internal part/item ID;
- physical location/bin;
- on-hand quantity;
- measured weight/volume;
- expiry/shelf-life where relevant;
- batch/lot;
- QR/barcode identity;
- physical count/audit events.

QR scenario:
scan -> identify exact item/location -> show physical quantity and key characteristics -> support permitted count/audit/update.

Boundary:
Warehouse physical truth is not the same as operational availability.

Example:
Warehouse: 1,200 on hand.
Operations Control Registry: 800 reserved, 400 available to promise.

Final KEEP/ABSORB decision remains deferred.
