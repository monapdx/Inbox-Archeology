import mailbox
from collections import defaultdict

mbox = mailbox.mbox("Personal-Love Letters(1).mbox")

threads = defaultdict(list)

for msg in mbox:
    sender = msg['from']
    subject = msg['subject'] or "No Subject"
    key = (sender, subject)

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode(errors="ignore")
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        except:
            pass

    threads[key].append(len(body))

# Score threads by depth + message size
scores = []
for (sender, subject), lengths in threads.items():
    score = len(lengths) * (sum(lengths) / max(len(lengths), 1))
    scores.append((score, sender, subject, len(lengths)))

# Sort by most “emotionally dense”
scores.sort(reverse=True)

# Show top candidates
for s in scores[:10]:
    print(s)