# GAACA Dataset — MikroTik CAPsMAN — MISCONFIGURED — Sample 5
/caps-man security add name=sec-open authentication-types="" encryption=""
/caps-man datapath add name=dp-open client-to-client-forwarding=yes
/caps-man configuration add name=cfg-open ssid=FreeWiFi security=sec-open datapath=dp-open
