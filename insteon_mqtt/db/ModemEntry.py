#===========================================================================
#
# Insteon PLM modem all link database entry
#
#===========================================================================
from ..Address import Address
from .. import log

LOG = log.get_logger()


class ModemEntry:
    @staticmethod
    def from_json(data):
        """Read a ModemEntry from a JSON input.

        The inverse of this is to_json().

        Args:
          data:    (dict): The data to read from.

        Returns:
          ModemEntry: Returns the created ModemEntry object.
        """
        return ModemEntry(Address.from_json(data['addr']),
                          data['group'],
                          data['is_controller'],
                          bytes(data['data']))

    #-----------------------------------------------------------------------
    def __init__(self, addr, group, is_controller, data=None):
        """Constructor

        Args:
          addr:            (Address) The device address.
          group:           (int) The group the device is part of.
          is_controller:   (bool) True if this device is a controller of addr,
                           False if this device is a responder of addr.
          data:            (bytes) 3 data bytes.  [0] is the on level, [1]
                           is the ramp rate.
        """
        data = data if data is not None else bytes(3)
        assert len(data) == 3

        # These should be these types but ctor them anyway to be sure.
        self.addr = Address(addr)
        self.group = int(group)
        self.is_controller = is_controller
        self.data = data

    #-----------------------------------------------------------------------
    def to_json(self):
        """Convert the entry to JSON format.

        Returns:
          (dict) Returns the entry as a JSON dictionary.
        """
        return {
            'addr' : self.addr.to_json(),
            'group' : self.group,
            'is_controller' : self.is_controller,
            'data' : list(self.data)
            }

    #-----------------------------------------------------------------------
    def __eq__(self, rhs):
        return (self.addr.id == rhs.addr.id and
                self.group == rhs.group and
                self.is_controller == rhs.is_controller)

    #-----------------------------------------------------------------------
    def __lt__(self, rhs):
        if self.addr.id != rhs.addr.id:
            return self.addr.id < rhs.addr.id

        return self.group < rhs.group

    #-----------------------------------------------------------------------
    def __str__(self):
        return "ID: %s  grp: %s  type: %s  data: %#04x %#04x %#04x" % \
            (self.addr.hex, self.group,
             'CTRL' if self.is_controller else 'RESP',
             self.data[0], self.data[1], self.data[2])

    #-----------------------------------------------------------------------
