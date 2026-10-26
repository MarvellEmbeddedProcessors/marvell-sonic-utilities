import os
import traceback
from unittest import mock
from mock import patch

from click.testing import CliRunner
from jsonpatch import JsonPatchConflict

import config.main as config
import show.main as show
import config.validated_config_db_connector as validated_config_db_connector
from utilities_common.db import Db
import utilities_common.bgp_util as bgp_util

ERROR_MSG = "Error: IP address is not valid"
NOT_EXIST_VLAN_ERROR_MSG ="does not exist"

INVALID_VRF_MSG ="""\
Usage: bind [OPTIONS] <interface_name> <vrf_name>
Try 'bind --help' for help.

Error: VRF Vrf2 does not exist!
"""

INVALID_MGMT_VRF_MSG ="""\
Usage: bind [OPTIONS] <interface_name> <vrf_name>
Try 'bind --help' for help.

Error: VRF mgmt does not exist!
"""

INVALID_VNET_MSG = """\
Usage: bind [OPTIONS] <interface_name> <vrf_name>
Try 'bind --help' for help.

Error: VNET Vnet_2000 does not exist!
"""

class TestConfigIP(object):
    _old_run_bgp_command = None

    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        cls._old_run_bgp_command = bgp_util.run_bgp_command
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=cls.mock_run_bgp_command())
        print("SETUP")

    ''' Tests for IPv4  '''

    def mock_run_bgp_command():
        return ""

    def test_add_vlan_interface_ipv4(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Vlan100 1.1.1.1/24  
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Vlan100", "1.1.1.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert NOT_EXIST_VLAN_ERROR_MSG in result.output

        # create vlan 4093
        result = runner.invoke(config.config.commands["vlan"].commands["add"], ["4093"], obj=db)
        # config int ip add Vlan4093 1.1.1.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Vlan4093", "1.1.1.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        # config int ip add Vlan000000000000003 1.1.1.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Vlan000000000000003", "1.1.1.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert NOT_EXIST_VLAN_ERROR_MSG in result.output

        # config int ip add Vlan1.2 1.1.1.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Vlan1.2", "1.1.1.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert NOT_EXIST_VLAN_ERROR_MSG in result.output

        # config int ip add Ethernet12 1.1.1.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Ethernet12", "1.1.1.1/24"],
                obj=obj)
        print(result.exit_code, result.output)
        assert "Interface Ethernet12 is a member of vlan" in result.output

        # config int ip add Ethernet12.10 1.1.1.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Ethernet12.10", "1.1.1.1/24"],
                obj=obj)
        print(result.exit_code, result.output)
        assert "Interface Ethernet12 is a member of vlan" in result.output

        # config int ip add PortChannel1001 1.1.1.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["PortChannel1001", "1.1.1.1/24"],
                obj=obj)
        print(result.exit_code, result.output)
        assert "Interface PortChannel1001 is a member of vlan" in result.output

        # config int ip add PortChannel1001.10 1.1.1.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["PortChannel1001.10", "1.1.1.1/24"],
                obj=obj)
        print(result.exit_code, result.output)
        assert "Interface PortChannel1001 is a member of vlan" in result.output


    def test_add_del_interface_valid_ipv4(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet0.10 10.11.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet0.10", "10.11.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet0.10', '10.11.10.1/24') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip add Eth36.10 32.11.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Eth36.10", "32.11.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Eth36.10', '32.11.10.1/24') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip add PortChannel0001.10 32.11.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["PortChannel0001.10", "32.11.10.1/24"],
                obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('PortChannel0001.10', '32.11.10.1/24') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip add Po0001.11 32.11.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Po0001.11", "32.11.10.1/24"],
                obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Po0001.11', '32.11.10.1/24') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip remove Ethernet64 10.10.10.1/24
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet0.10 10.11.10.1/24
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet0.10", "10.11.10.1/24"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet0.10', '10.11.10.1/24') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip remove Eth36.10 32.11.10.1/24
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"],
                                   ["Eth36.10", "32.11.10.1/24"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Eth36.10', '32.11.10.1/24') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Eth36.10", "32.11.10.1/24"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Eth36.10', '32.11.10.1/24') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip remove PortChannel0001.10 10.11.10.1/24
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(
                    config.config.commands["interface"].commands["ip"].commands["remove"],
                    ["PortChannel0001.10", "10.11.10.1/24"],
                    obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('PortChannel0001.10', '10.11.10.1/24') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip remove Po0001.11 32.11.10.1/24
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"],
                                   ["Po0001.11", "32.11.10.1/24"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Po0001.11', '32.11.10.1/24') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip add vlan1000 10.21.20.1/24 as secondary
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"],
                               ["Vlan1000", "10.11.20.1/24", "--secondary"], obj=obj)
        assert result.exit_code == 0
        assert ('Vlan1000', '10.11.20.1/24') in db.cfgdb.get_table('VLAN_INTERFACE')
        assert db.cfgdb.get_table('VLAN_INTERFACE')[('Vlan1000', '10.11.20.1/24')]['secondary'] == "true"

        # config int ip add vlan2000 10.21.20.1/24 as secondary
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"],
                               ["Vlan2000", "10.21.20.1/24", "-s"], obj=obj)
        assert result.exit_code == 0
        assert ('Vlan2000', '10.21.20.1/24') in db.cfgdb.get_table('VLAN_INTERFACE')
        assert db.cfgdb.get_table('VLAN_INTERFACE')[('Vlan2000', '10.21.20.1/24')]['secondary'] == "true"

        # config int ip add vlan4000 10.16.20.1/24 as primary and make sure secondary is not present in table
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"],
                               ["Vlan4000", "10.16.20.1/24"], obj=obj)
        assert result.exit_code == 0
        assert ('Vlan4000', '10.16.20.1/24') in db.cfgdb.get_table('VLAN_INTERFACE')
        assert 'secondary' not in db.cfgdb.get_table('VLAN_INTERFACE')[('Vlan4000', '10.16.20.1/24')]

        # create vlan 500
        result = runner.invoke(config.config.commands["vlan"].commands["add"], ["500"], obj=db)
        # config int ip add vlan500 10.21.20.1/24 as secondary - should fail as vlan500 is not added in table
        ERR_MSG = "Error: Primary for the interface Vlan500 is not set, so skipping adding the interface"
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"],
                               ["Vlan500", "10.21.20.1/24", "--secondary"], obj=obj)
        assert result.exit_code != 0
        assert ERR_MSG in result.output

    def test_add_interface_invalid_ipv4(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10000.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10000.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ERROR_MSG in result.output

    def test_add_interface_ipv4_invalid_mask(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/37
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/37"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ERROR_MSG in result.output

    def test_add_interface_ipv4_with_leading_zeros(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet68 10.10.10.002/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet68", "10.10.10.0002/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ERROR_MSG in result.output

    def test_ip_add_on_interface_which_is_member_of_portchannel(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet32 100.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet32", "100.10.10.1/24"], obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Ethernet32 is configured as a member of portchannel.' in result.output

        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Ethernet32.10", "100.10.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Ethernet32 is configured as a member of portchannel.' in result.output

        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Eth32.10", "100.10.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Ethernet32 is configured as a member of portchannel.' in result.output

    def test_ip_add_on_interface_with_no_port(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db': db.cfgdb}

        # config int ip add Ethernet51 100.10.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Ethernet51", "100.10.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Interface Ethernet51 does not exist' in result.output

        # config int ip add Ethernet51.10 100.10.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Ethernet51.10", "100.10.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Interface Ethernet51.10 does not exist' in result.output

        # config int ip add Eth51.10 32.11.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Eth51.10", "32.11.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Interface Eth51.10 does not exist' in result.output

        # config int ip add PortChanne51.10 32.11.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["PortChannel51.10", "32.11.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Interface PortChannel51.10 does not exist' in result.output

        # config int ip add Po51.10 32.11.10.1/24
        result = runner.invoke(
                config.config.commands["interface"].commands["ip"].commands["add"],
                ["Po51.10", "32.11.10.1/24"],
                obj=obj)
        assert result.exit_code != 0
        print(result.output)
        print(result.exit_code)
        assert 'Error: Interface Po51.10 does not exist' in result.output


    '''  Tests for IPv6 '''

    def test_add_del_interface_valid_ipv6(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet72 2001:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet72", "2001:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet72', '2001:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34') in db.cfgdb.get_table('INTERFACE')

        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet0.10", "1010:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet0.10', '1010:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Eth36.10", "3210:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Eth36.10', '3210:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        # config int ip remove Ethernet72 2001:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet72", "2001:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet72', '2001:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34') not in db.cfgdb.get_table('INTERFACE')

        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet0.10", "1010:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet0.10', '1010:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Eth36.10", "3210:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Eth36.10', '3210:1db8:11a3:19d7:1f34:8a2e:17a0:765d/34') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

    def test_del_interface_case_sensitive_ipv6(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        obj['config_db'].set_entry('INTERFACE', ('Ethernet72', 'FC00::1/126'), {})
        assert ('Ethernet72', 'FC00::1/126') in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet72 FC00::1/126
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet72", "FC00::1/126"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet72', 'FC00::1/126') not in db.cfgdb.get_table('INTERFACE')

    def test_add_interface_invalid_ipv6(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet72 20001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/34
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet72", "20001:0db8:11a3:19d7:1f34:8a2e:17a0:765d/34"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ERROR_MSG in result.output

    def test_add_interface_ipv6_invalid_mask(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet72 2001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/200
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet72", "2001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/200"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ERROR_MSG in result.output

    def test_add_del_interface_ipv6_with_leading_zeros(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet68 2001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/34
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet68", "2001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/34"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet68', '2001:db8:11a3:9d7:1f34:8a2e:7a0:765d/34') in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet68 2001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/34
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet68", "2001:0db8:11a3:09d7:1f34:8a2e:07a0:765d/34"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet68', '2001:db8:11a3:9d7:1f34:8a2e:7a0:765d/34') not in db.cfgdb.get_table('INTERFACE')

    def test_add_del_interface_shortened_ipv6_with_leading_zeros(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet68 3000::001/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet68", "3000::001/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet68', '3000::1/64') in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet68 3000::001/64
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet68", "3000::001/64"], obj=obj)
            print(result.exit_code, result.output)
            assert result.exit_code == 0
            assert mock_run_command.call_count == 1
            assert ('Ethernet68', '3000::1/64') not in db.cfgdb.get_table('INTERFACE')

    def test_intf_vrf_bind_unbind(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb, 'namespace':db.db.namespace}

        result = runner.invoke(config.config.commands["interface"].commands["vrf"].commands["bind"], ["Ethernet64", "Vrf1"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        result = runner.invoke(config.config.commands["interface"].commands["vrf"].commands["unbind"], ["Ethernet64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

    def test_intf_vnet_bind_unbind(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db': db.cfgdb, 'namespace': db.db.namespace}

        db.cfgdb.set_entry("VXLAN_TUNNEL", "tunnel1", {"src_ip": "10.1.0.1", "dst_port": "4789"})

        # Create vnet
        result = runner.invoke(config.config.commands["vnet"].commands["add"], ["Vnet_1000", "222", "tunnel1"], obj=db)
        print(db.cfgdb.get_table('VNET'))
        assert ('Vnet_1000') in db.cfgdb.get_table('VNET')
        assert result.exit_code == 0

        bind_command = config.config.commands["interface"].commands["vrf"].commands["bind"]
        interfaces = ["Ethernet64", "Vnet_1000"]
        result = runner.invoke(bind_command, interfaces, obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        unbind_command = config.config.commands["interface"].commands["vrf"].commands["unbind"]
        interfaces = ["Ethernet64"]
        result = runner.invoke(unbind_command, interfaces, obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

    def test_intf_unknown_vrf_bind(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb, 'namespace':db.db.namespace}

        result = runner.invoke(config.config.commands["interface"].commands["vrf"].commands["bind"], ["Ethernet64", "Vrf2"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert result.output == INVALID_VRF_MSG

        bind_command = config.config.commands["interface"].commands["vrf"].commands["bind"]
        interfaces = ["Ethernet64", "Vnet_2000"]
        result = runner.invoke(bind_command, interfaces, obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert result.output == INVALID_VNET_MSG

        result = runner.invoke(config.config.commands["interface"].commands["vrf"].commands["bind"], ["Ethernet64", "mgmt"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert result.output == INVALID_MGMT_VRF_MSG
        
        result = runner.invoke(config.config.commands["vrf"].commands["add"], ["mgmt"], obj=obj)
        print(result.exit_code, result.output)
        result = runner.invoke(config.config.commands["interface"].commands["vrf"].commands["bind"], ["Ethernet64", "mgmt"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

    @patch("config.validated_config_db_connector.ValidatedConfigDBConnector.validated_mod_entry", mock.Mock(side_effect=ValueError))
    @patch("config.validated_config_db_connector.ValidatedConfigDBConnector.validated_set_entry", mock.Mock(side_effect=ValueError))
    @patch("validated_config_db_connector.device_info.is_yang_config_validation_enabled", mock.Mock(return_value=True))
    @patch("config.main.ConfigDBConnector.get_entry", mock.Mock(return_value={"mgmtVrfEnabled": "false"}))
    def test_add_vrf_invalid_configdb_yang_validation(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb, 'namespace':db.db.namespace}
        
        result = runner.invoke(config.config.commands["vrf"].commands["add"], ["mgmt"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert "Invalid ConfigDB. Error" in result.output
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["vrf"].commands["add"], ["Vrf01"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert "Invalid ConfigDB. Error" in result.output
        assert result.exit_code != 0
    
    @patch("config.validated_config_db_connector.ValidatedConfigDBConnector.validated_mod_entry", mock.Mock(side_effect=ValueError))
    @patch("config.validated_config_db_connector.ValidatedConfigDBConnector.validated_set_entry", mock.Mock(side_effect=JsonPatchConflict))
    @patch("validated_config_db_connector.device_info.is_yang_config_validation_enabled", mock.Mock(return_value=True))
    @patch("config.main.is_vrf_exists", mock.Mock(return_value=True))
    @patch("config.main.ConfigDBConnector.get_entry", mock.Mock(return_value={"mgmtVrfEnabled": "true"}))
    def test_del_vrf_invalid_configdb_yang_validation(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb, 'namespace':db.db.namespace}

        result = runner.invoke(config.config.commands["vrf"].commands["del"], ["mgmt"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert "Invalid ConfigDB. Error" in result.output
        assert result.exit_code != 0 

        result = runner.invoke(config.config.commands["vrf"].commands["del"], ["Vrf01"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert "Invalid ConfigDB. Error" in result.output
        assert result.exit_code != 0
    
    @classmethod
    def teardown_class(cls):
        bgp_util.run_bgp_command = cls._old_run_bgp_command
        print("TEARDOWN")


class TestConfigMgmtIP(object):
    PRIMARY = ("eth0", "10.28.32.214/23")
    SECONDARY = ("eth0", "10.28.32.110/23")
    PRIMARY_V6 = ("eth0", "2603:10e2:0:2902::8/64")
    SECONDARY_V6 = ("eth0", "2603:10e2:0:2902::9/64")

    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"

    def _setup(self):
        db = Db()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.PRIMARY, {"gwaddr": "10.28.32.1"})
        return db, CliRunner(), {'config_db': db.cfgdb}

    def _add(self, runner, obj, args):
        cfgdb = obj['config_db']
        with mock.patch("config.main._get_all_mgmtinterface_keys",
                        side_effect=lambda: list(cfgdb.get_table("MGMT_INTERFACE").keys())):
            return runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], args, obj=obj)

    def _remove(self, runner, obj, args):
        return runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], args, obj=obj)

    def test_add_secondary_keeps_primary(self):
        db, runner, obj = self._setup()
        result = self._add(runner, obj, ["eth0", self.SECONDARY[1], "--secondary"])
        assert result.exit_code == 0, result.output
        table = db.cfgdb.get_table("MGMT_INTERFACE")
        assert table[self.PRIMARY] == {"gwaddr": "10.28.32.1"}
        assert table[self.SECONDARY] == {"secondary": "true"}

    def test_add_secondary_duplicate_host_rejected(self):
        db, runner, obj = self._setup()
        result = self._add(runner, obj, ["eth0", "10.28.32.214/24", "--secondary"])
        assert result.exit_code != 0
        assert "already configured on eth0" in result.output
        assert ("eth0", "10.28.32.214/24") not in db.cfgdb.get_table("MGMT_INTERFACE")

    def test_add_secondary_without_primary_rejected(self):
        db = Db()
        runner = CliRunner()
        result = self._add(runner, {'config_db': db.cfgdb}, ["eth0", self.SECONDARY[1], "--secondary"])
        assert result.exit_code != 0
        assert "Primary for the interface eth0 is not set" in result.output
        assert self.SECONDARY not in db.cfgdb.get_table("MGMT_INTERFACE")

    def test_add_secondary_with_gateway_rejected(self):
        db, runner, obj = self._setup()
        result = self._add(runner, obj, ["eth0", self.SECONDARY[1], "10.28.32.1", "--secondary"])
        assert result.exit_code != 0
        assert "A gateway cannot be set with --secondary" in result.output
        assert self.SECONDARY not in db.cfgdb.get_table("MGMT_INTERFACE")

    def test_replace_primary_keeps_secondary(self):
        db, runner, obj = self._setup()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.SECONDARY, {"secondary": "true"})
        result = self._add(runner, obj, ["eth0", "10.28.32.215/23", "10.28.32.1"])
        assert result.exit_code == 0, result.output
        table = db.cfgdb.get_table("MGMT_INTERFACE")
        assert self.PRIMARY not in table
        assert table[("eth0", "10.28.32.215/23")] == {"gwaddr": "10.28.32.1"}
        assert table[self.SECONDARY] == {"secondary": "true"}

    def test_remove_primary_with_secondary_rejected(self):
        db, runner, obj = self._setup()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.SECONDARY, {"secondary": "true"})
        result = self._remove(runner, obj, ["eth0", self.PRIMARY[1]])
        assert result.exit_code != 0
        assert "remove it before removing primary" in result.output
        assert self.PRIMARY in db.cfgdb.get_table("MGMT_INTERFACE")

        result = self._remove(runner, obj, ["eth0", self.SECONDARY[1]])
        assert result.exit_code == 0, result.output
        result = self._remove(runner, obj, ["eth0", self.PRIMARY[1]])
        assert result.exit_code == 0, result.output
        assert db.cfgdb.get_table("MGMT_INTERFACE") == {}

    def test_show_mgmt_address_secondary_uses_primary_gateway(self):
        db, runner, _ = self._setup()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.SECONDARY, {"secondary": "true"})
        result = self._show(runner, db)
        assert result.exit_code == 0, result.output
        assert result.output == (
            "Management IP address = 10.28.32.110/23\n"
            "Management Network Default Gateway = 10.28.32.1\n"
            "Management IP address = 10.28.32.214/23\n"
            "Management Network Default Gateway = 10.28.32.1\n"
        )

    def _show(self, runner, db):
        mock_db = mock.Mock(get_table=lambda table: db.cfgdb.get_table(table))
        with mock.patch("show.main.ConfigDBConnector", return_value=mock_db):
            return runner.invoke(show.cli.commands["management_interface"].commands["address"], [])

    def test_add_ipv6_secondary(self):
        db, runner, obj = self._setup()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.PRIMARY_V6, {"gwaddr": "2603:10e2:0:2902::1"})
        result = self._add(runner, obj, ["eth0", self.SECONDARY_V6[1], "--secondary"])
        assert result.exit_code == 0, result.output
        table = db.cfgdb.get_table("MGMT_INTERFACE")
        assert table[self.PRIMARY] == {"gwaddr": "10.28.32.1"}
        assert table[self.PRIMARY_V6] == {"gwaddr": "2603:10e2:0:2902::1"}
        assert table[self.SECONDARY_V6] == {"secondary": "true"}

        # The IPv6 secondary shows the IPv6 primary's gateway, not the IPv4 one
        result = self._show(runner, db)
        assert result.exit_code == 0, result.output
        assert ("Management IP address = 2603:10e2:0:2902::9/64\n"
                "Management Network Default Gateway = 2603:10e2:0:2902::1\n") in result.output

    def test_add_ipv6_secondary_with_only_ipv4_primary_rejected(self):
        db, runner, obj = self._setup()
        result = self._add(runner, obj, ["eth0", self.SECONDARY_V6[1], "--secondary"])
        assert result.exit_code != 0
        assert "Primary for the interface eth0 is not set" in result.output
        assert self.SECONDARY_V6 not in db.cfgdb.get_table("MGMT_INTERFACE")

    def test_add_multiple_secondaries(self):
        db, runner, obj = self._setup()
        second = ("eth0", "10.28.32.111/23")
        other_subnet = ("eth0", "10.29.0.5/24")
        for entry in (self.SECONDARY, second, other_subnet):
            result = self._add(runner, obj, ["eth0", entry[1], "--secondary"])
            assert result.exit_code == 0, result.output
        table = db.cfgdb.get_table("MGMT_INTERFACE")
        assert table[self.PRIMARY] == {"gwaddr": "10.28.32.1"}
        for entry in (self.SECONDARY, second, other_subnet):
            assert table[entry] == {"secondary": "true"}

    def test_add_primary_equal_to_existing_secondary(self):
        db, runner, obj = self._setup()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.SECONDARY, {"secondary": "true"})
        result = self._add(runner, obj, ["eth0", self.SECONDARY[1], "10.28.32.1"])
        assert result.exit_code == 0, result.output
        # The old primary is replaced and the address is now the primary, not a secondary
        assert db.cfgdb.get_table("MGMT_INTERFACE") == {self.SECONDARY: {"gwaddr": "10.28.32.1"}}

    def test_remove_only_secondary(self):
        db, runner, obj = self._setup()
        db.cfgdb.set_entry("MGMT_INTERFACE", self.SECONDARY, {"secondary": "true"})
        result = self._remove(runner, obj, ["eth0", self.SECONDARY[1]])
        assert result.exit_code == 0, result.output
        assert db.cfgdb.get_table("MGMT_INTERFACE") == {self.PRIMARY: {"gwaddr": "10.28.32.1"}}

    def test_primary_without_gateway_then_secondary(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = self._add(runner, obj, ["eth0", self.PRIMARY[1]])
        assert result.exit_code == 0, result.output
        assert self.PRIMARY in db.cfgdb.get_table("MGMT_INTERFACE")
        assert "gwaddr" not in db.cfgdb.get_table("MGMT_INTERFACE")[self.PRIMARY]

        result = self._show(runner, db)
        assert result.exit_code == 0, result.output
        assert result.output == "Management IP address = 10.28.32.214/23\n"

        result = self._add(runner, obj, ["eth0", self.SECONDARY[1], "--secondary"])
        assert result.exit_code == 0, result.output
        assert db.cfgdb.get_table("MGMT_INTERFACE")[self.SECONDARY] == {"secondary": "true"}

        result = self._show(runner, db)
        assert result.exit_code == 0, result.output
        assert result.output == (
            "Management IP address = 10.28.32.110/23\n"
            "Management IP address = 10.28.32.214/23\n"
        )
