-- prosody.cfg.lua
admins = { }

use_tls = false

modules_enabled = {
    "roster";
    "saslauth";
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

VirtualHost "xmpp"
    enabled = true
    allow_registration = true
    authentication = "internal_plain"
    use_tls = false
    c2s_require_encryption = false
