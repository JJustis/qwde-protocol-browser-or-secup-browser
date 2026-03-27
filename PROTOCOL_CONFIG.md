# QWDE Protocol - Custom Protocol Configuration

## Change the Protocol Prefix

You can customize the protocol prefix from `qwde://` to anything you want!

### How to Change

1. Open `qwde_config.ini`
2. Find the `[protocol]` section
3. Change `protocol_prefix` to your desired value

### Example Configurations

```ini
[protocol]
# Use qwde://
protocol_prefix = qwde
protocol_separator = ://
```

```ini
[protocol]
# Use this://
protocol_prefix = this
protocol_separator = ://
```

```ini
[protocol]
# Use mysite://
protocol_prefix = mysite
protocol_separator = ://
```

```ini
[protocol]
# Use secure://
protocol_prefix = secure
protocol_separator = ://
```

```ini
[protocol]
# Use custom://
protocol_prefix = custom
protocol_separator = ://
```

### Available Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `protocol_prefix` | The prefix before `://` | `qwde` |
| `protocol_separator` | The separator after prefix | `://` |

### Full Protocol Format

The full protocol is constructed as:
```
{protocol_prefix}{protocol_separator}
```

So with:
```ini
protocol_prefix = qwde
protocol_separator = ://
```

Result: `qwde://`

### Usage Examples

After configuration, use your custom protocol:

**With `qwde://`:**
```
qwde://mysite.qwde
qwede://fwild:123
```

**With `this://`:**
```
this://mysite
this://fwild:42
```

**With `secure://`:**
```
secure://mydomain
secure://fwild:99
```

### In the Browser

The browser will automatically:
1. Read the protocol from config
2. Add the protocol prefix to URLs you type
3. Display the correct protocol in the URL bar
4. Handle protocol validation

### Programmatic Use

```python
from qwde_protocol_handler import (
    get_protocol,
    get_protocol_prefix,
    add_protocol,
    create_url,
    is_valid_url,
    parse_url
)

# Get current protocol
protocol = get_protocol()  # Returns: "qwde://"

# Get prefix
prefix = get_protocol_prefix()  # Returns: "qwde"

# Add protocol to URL
url = add_protocol("mysite")  # Returns: "qwde://mysite"

# Create URL
url = create_url("domain.com")  # Returns: "qwede://domain.com"
fwild_url = create_url("123", "fwild")  # Returns: "qwede://fwild:123"

# Check if valid
is_valid = is_valid_url("qwede://test")  # Returns: True

# Parse URL
parsed = parse_url("qwede://mysite.qwde")
# Returns: {
#   'protocol': 'qwede://',
#   'target': 'mysite.qwde',
#   'type': 'domain',
#   'domain': 'mysite.qwde'
# }
```

### Changing at Runtime

You can also change the protocol programmatically:

```python
from qwde_protocol_handler import get_protocol_handler

handler = get_protocol_handler()

# Change prefix
handler.set_protocol_prefix('this')

# Now all URLs will use this://
new_protocol = handler.get_full_protocol()  # Returns: "this://"
```

**Note:** After changing programmatically, you may need to restart the browser for changes to take full effect.

### Rebuilding with Custom Protocol

If you want to distribute with a custom protocol:

1. Edit `qwde_config.ini` with your desired prefix
2. Rebuild: `build_all.bat`
3. The EXE will use your custom protocol

### Examples by Use Case

**Personal Network:**
```ini
protocol_prefix = mynet
# Results in: mynet://
```

**Company Internal:**
```ini
protocol_prefix = internal
# Results in: internal://
```

**Secure Network:**
```ini
protocol_prefix = secure
# Results in: secure://
```

**Testing:**
```ini
protocol_prefix = test
# Results in: test://
```

**Branded:**
```ini
protocol_prefix = yourbrand
# Results in: yourbrand://
```

---

**Configuration File:** `qwde_config.ini`  
**Section:** `[protocol]`  
**Last Updated:** 2026-03-27
