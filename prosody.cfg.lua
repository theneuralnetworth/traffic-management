-- prosody.cfg.lua
admins = { }

modules_enabled = {
    "roster";
    "saslauth";
    "tls";
    "dialback";
    "disco";
    "private";
    "vcard";
    "version";
    "uptime";
    "time";
    "ping";
    "register";
    "admin_adhoc";
}

allow_registration = true
authentication = "internal_plain"

c2s_require_encryption = false

VirtualHost "localhost"
    enabled = true
