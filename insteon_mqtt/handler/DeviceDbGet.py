#===========================================================================
#
# Device get all link database handler.
#
#===========================================================================
# pylint: disable=too-many-return-statements
from .. import log
from .. import message as Msg
from .Base import Base

LOG = log.get_logger()


class DeviceDbGet(Base):
    """Device database request message handler.

    To download the all link database from a device, we send a
    request.  The output message gets ACK'ed back to us.  Then the
    device sends us a series of messages with the database entries.
    The last message will be all zeros to indicate no more records.

    Each reply is passed to the callback function set in the
    constructor which is usually a method on the device to update it's
    database.
    """
    def __init__(self, device_db, on_done):
        """Constructor

        Args
          addr:    (Address) The address of the device we're expecting
        TODO
          callback: Callback function to pass database messages to or None
                    to indicate the end of the entries.
        """
        super().__init__(on_done=on_done)

        self.db = device_db

    #-----------------------------------------------------------------------
    def msg_received(self, protocol, msg):
        """See if we can handle the message.

        See if the message is the expected ACK of our output or the
        expected database reply message.  If we get a reply, pass it
        to the device to update it's database with the info.

        Args:
          protocol:  (Protocol) The Insteon Protocol object
          msg:       Insteon message object that was read.

        Returns:
          Msg.UNKNOWN if we can't handle this message.
          Msg.CONTINUE if we handled the message and expect more.
          Msg.FINISHED if we handled the message and are done.
        """
        # Import here - at file scope this makes a circular import
        # which is ok in Python>=3.5 but not 3.4.
        from .. import db

        # Probably an echo back of our sent message.  See if the
        # message matches the address we sent to and assume it's the
        # ACK/NAK message.  These seem to be either extended or
        # standard message so allow for both.
        if isinstance(msg, (Msg.OutExtended, Msg.OutStandard)):
            if msg.to_addr == self.db.addr and msg.cmd1 == 0x2f:
                if not msg.is_ack:
                    LOG.error("%s NAK response", self.db.addr)
                return Msg.CONTINUE

            return Msg.UNKNOWN

        # Probably an ACK/NAK from the device for our get command.
        elif isinstance(msg, Msg.InpStandard):
            # Filter by address and command.
            if msg.from_addr != self.db.addr or msg.cmd1 != 0x2f:
                return Msg.UNKNOWN

            if msg.flags.type == Msg.Flags.Type.DIRECT_ACK:
                LOG.info("%s device ACK response", msg.from_addr)
                return Msg.CONTINUE

            elif msg.flags.type == Msg.Flags.Type.DIRECT_NAK:
                LOG.error("%s device NAK error: %s", msg.from_addr, msg)
                self.on_done(False, "Database command NAK")
                return Msg.FINISHED

            else:
                LOG.warning("%s device unexpected msg: %s", msg.from_addr, msg)
                return Msg.UNKNOWN

        # Process the real reply.  Database reply is an extended messages.
        elif isinstance(msg, Msg.InpExtended):
            # Filter by address and command.
            if msg.from_addr != self.db.addr or msg.cmd1 != 0x2f:
                return Msg.UNKNOWN

            # Convert the message to a database device entry.
            entry = db.DeviceEntry.from_bytes(msg.data)

            # Skip entries w/ a null memory location.
            if entry.mem_loc:
                self.db.add_entry(entry)

            # Note that if the entry is a null entry (all zeros), then
            # is_last_rec will be True as well.
            if entry.db_flags.is_last_rec:
                self.on_done(True, "Database received")
                return Msg.FINISHED

            # Otherwise keep processing records as they arrive.
            else:
                return Msg.CONTINUE

        return Msg.UNKNOWN

    #-----------------------------------------------------------------------
