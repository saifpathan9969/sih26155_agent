# GAACA Dataset — MikroTik CAPsMAN — SECURE — Sample 19
/caps-man security add name=sec-prof authentication-types=wpa2-eap,wpa3-eap encryption=aes-ccm
/caps-man datapath add name=dp-secure client-to-client-forwarding=no local-forwarding=no
/caps-man configuration add name=cfg-secure ssid=MikroTik-Enterprise security=sec-prof datapath=dp-secure
