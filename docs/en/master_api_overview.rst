.. _modbus_api_master_overview:

Modbus Master API Overview
--------------------------

The following overview describes how to setup Modbus master communication. The overview reflects a typical programming workflow and is broken down into the sections provided below:

1. :ref:`modbus_api_port_initialization` - Initialization of Modbus controller interface for the selected port.
2. :ref:`modbus_api_master_configure_descriptor` - Configure data descriptors to access slave parameters.
3. :ref:`modbus_api_master_setup_communication_options` - Allows to setup communication options for selected port.
4. :ref:`modbus_api_master_start_communication` - Start stack and sending / receiving data.
5. :ref:`modbus_api_master_destroy` - Destroy Modbus controller and its resources.

.. _modbus_api_master_configure_descriptor:

Configuring Master Data Access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The architectural approach of ESP_Modbus includes one level above standard Modbus IO driver. The additional layer is called Modbus controller and its goal is to add an abstraction such as CID - characteristic identifier. The CID is linked to a corresponding Modbus registers through the table called Data Dictionary and represents device physical parameter (such as temperature, humidity, etc.) in specific Modbus slave device. This approach allows the upper layer (e.g., MESH or MQTT) to be isolated from Modbus specifics thus simplify Modbus integration with other protocols/networks.

The Data Dictionary is the list in the Modbus master which shall be defined by user to link each CID to its corresponding Modbus registers representation using Register Mapping table of the Modbus slave being used.
Each element in this data dictionary is of type :cpp:type:`mb_parameter_descriptor_t` and represents the description of one physical characteristic:

.. list-table:: Table 1 Modbus master Data Dictionary description
  :widths: 8 10 82
  :header-rows: 1

  * - Field 
    - Description
    - Detailed information
  * - ``cid``
    - Characteristic ID         
    - The identifier of characteristic (must be unique).
  * - ``param_key``
    - Characteristic Name
    - String description of the characteristic.
  * - ``param_units``
    - Characteristic Units
    - Physical Units of the characteristic.
  * - ``mb_slave_addr``
    - Modbus Slave Address
    - The short address of the device with correspond parameter UID.
  * - ``mb_param_type``
    - Modbus Register Type
    - Type of Modbus register area. 
      :cpp:enumerator:`MB_PARAM_INPUT`, :cpp:enumerator:`MB_PARAM_HOLDING`, :cpp:enumerator:`MB_PARAM_COIL`, :cpp:enumerator:`MB_PARAM_DISCRETE`  - represents Input , Holding, Coil and Discrete input register area accordingly;
  * - ``mb_reg_start``
    - Modbus Register Start
    - Relative register address of the characteristic in the register area.  
  * - ``mb_size``
    - Modbus Register Size
    - Length of characteristic in registers (two bytes).
  * - ``param_offset``
    - Instance Offset
    - Offset to instance of the characteristic in bytes. It is used to calculate the absolute address to the characteristic in the storage structure.
      It is optional field and can be set to zero if the parameter is not used in the application.
  * - ``param_type``
    - Data Type
    - Specifies type of the characteristic. Possible types are described in the section :ref:`modbus_mapping_complex_data_types`.
  * - ``param_size``
    - Data Size
    - The storage size of the characteristic (in bytes) describes the size of data to keep into data instance during mapping. For the :ref:`modbus_mapping_complex_data_types` this allows to define the data container of the corresponded type.
  * - ``param_opts``
    - Parameter Options
    - Limits, options of characteristic used during processing of alarm in user application (optional)
  * - ``access``
    - Parameter access type
    - Can be used in user application to define the behavior of the characteristic during processing of data in user application;
      :cpp:enumerator:`PAR_PERMS_READ_WRITE_TRIGGER`, :cpp:enumerator:`PAR_PERMS_READ`, :cpp:enumerator:`PAR_PERMS_READ_WRITE_TRIGGER`;

.. note:: The ``cid`` and ``param_key`` have to be unique. Please use the prefix to the parameter key if you have several similar parameters in your register map table.

Examples Of Mapping
@@@@@@@@@@@@@@@@@@@

Please refer to section :ref:`modbus_mapping_complex_data_types` for more information about used data types.

Example 1: Configure access to legacy parameter types is described below.

.. list-table:: Table 2 Example Register mapping table of Modbus slave
  :widths: 5 5 2 10 5 5 68
  :header-rows: 1
  
  * - CID
    - Register
    - Length
    - Range
    - Type
    - Units
    - Description
  * - 0
    - 30000
    - 4
    - MAX_UINT
    - U32
    - Not defined
    - Serial number of device (4 bytes) read-only
  * - 1
    - 30002
    - 2
    - MAX_UINT
    - U16
    - Not defined
    - Software version (4 bytes) read-only
  * - 2
    - 40000
    - 4
    - -20..40
    - FLOAT
    - DegC
    - Room temperature in DegC. Writing a temperature value to this register for single point calibration.
  * - 3
    - 40002
    - 16
    - 1..100 bytes
    - ASCII or binary array
    - Not defined
    - Device name (16 bytes) ASCII string. The type of `PARAM_TYPE_ASCII` allows to read/write complex parameter (string or binary data) that corresponds to one CID.

.. code:: c

    // Enumeration of modbus slave addresses accessed by master device
    enum {
        MB_DEVICE_ADDR1 = 1,
        MB_DEVICE_ADDR2,
        MB_SLAVE_COUNT
    };

    // Enumeration of all supported CIDs for device
    enum {
        CID_SER_NUM1 = 0,
        CID_SW_VER1,
        CID_DEV_NAME1,
        CID_TEMP_DATA_1,
        CID_SER_NUM2,
        CID_SW_VER2,
        CID_DEV_NAME2,
        CID_TEMP_DATA_2
    };

    // Example Data Dictionary for Modbus parameters in 2 slaves in the segment
    mb_parameter_descriptor_t device_parameters[] = {
        // CID, Name, Units, Modbus addr, register type, Modbus Reg Start Addr, Modbus Reg read length, 
        // Instance offset (NA), Instance type, Instance length (bytes), Options (NA), Permissions
        { CID_SER_NUM1, STR("Serial_number_1"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_INPUT, 0, 2,
                        0, PARAM_TYPE_U32, 4, OPTS( 0,0,0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_SW_VER1, STR("Software_version_1"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_INPUT, 2, 1,
                        0, PARAM_TYPE_U16, 2, OPTS( 0,0,0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_DEV_NAME1, STR("Device name"), STR("__"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING, 2, 8,
                        0, PARAM_TYPE_ASCII, 16, OPTS( 0, 0, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_TEMP_DATA_1, STR("Temperature_1"), STR("C"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING, 0, 2,
                        0, PARAM_TYPE_FLOAT, 4, OPTS( 16, 30, 1 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_SER_NUM2, STR("Serial_number_2"), STR("--"), MB_DEVICE_ADDR2, MB_PARAM_INPUT, 0, 2,
                        0, PARAM_TYPE_U32, 4, OPTS( 0,0,0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_SW_VER2, STR("Software_version_2"), STR("--"), MB_DEVICE_ADDR2, MB_PARAM_INPUT, 2, 1,
                        0, PARAM_TYPE_U16, 2, OPTS( 0,0,0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_DEV_NAME2, STR("Device name"), STR("__"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING, 2, 8,
                        0, PARAM_TYPE_ASCII, 16, OPTS( 0, 0, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_TEMP_DATA_2, STR("Temperature_2"), STR("C"), MB_DEVICE_ADDR2, MB_PARAM_HOLDING, 0, 2,
                        0, PARAM_TYPE_FLOAT, 4, OPTS( 20, 30, 1 ), PAR_PERMS_READ_WRITE_TRIGGER },
    };
    // Calculate number of parameters in the table
    uint16_t num_device_parameters = (sizeof(device_parameters) / sizeof(device_parameters[0]));

Example 2: Configure access using extended parameter types for third-party devices.

.. list-table:: Table 3 Example Register mapping table of Modbus slave
  :widths: 2 4 2 10 3 68
  :header-rows: 1
  
  * - CID
    - Register
    - Length
    - Range
    - Units
    - Description
  * - 0
    - 40000
    - 4
    - 0 ... 255
    - No units
    - :cpp:enumerator:`PARAM_TYPE_U8_A` - unsigned integer 8-bit
  * - 1
    - 40002
    - 4
    - 0 ... 65535
    - No Units
    - :cpp:enumerator:`PARAM_TYPE_U16_AB` uinsigned integer 16-bit
  * - 3
    - 40004
    - 8
    - 0 ... Unsigned integer 32-bit range
    - No units
    - :cpp:enumerator:`PARAM_TYPE_U32_ABCD` - unsigned integer 32-bit in ABCD format
  * - 4
    - 40008
    - 8
    - 0 ... Unsigned integer 32-bit range
    - No units
    - :cpp:enumerator:`PARAM_TYPE_FLOAT_CDAB` - FLOAT 32-bit value in CDAB format
  * - 5
    - 400012
    - 16
    - 0 ... Unsigned integer 64-bit range
    - No units
    - :cpp:enumerator:`PARAM_TYPE_U64_ABCDEFGH` - Unsigned integer 64-bit value in ABCDEFGH format
  * - 6
    - 400020
    - 16
    - 0 ... Unsigned integer 64-bit range
    - No units
    - :cpp:enumerator:`PARAM_TYPE_DOUBLE_HGFEDCBA` - Double precision 64-bit value in HGFEDCBA format

.. code:: c

    #include "limits.h"
    #include "mbcontroller.h"
    
    #define HOLD_OFFSET(field) ((uint16_t)(offsetof(holding_reg_params_t, field) + 1))
    #define HOLD_REG_START(field) (HOLD_OFFSET(field) >> 1)
    #define HOLD_REG_SIZE(field) (sizeof(((holding_reg_params_t *)0)->field) >> 1)

    #pragma pack(push, 1)
    // Example structure that contains parameter arrays of different types
    // with different options of endianness.
    typedef struct
    {
        uint16_t holding_u8_a[2];
        uint16_t holding_u16_ab[2];
        uint32_t holding_uint32_abcd[2];
        float holding_float_cdab[2];
        double holding_uint64_abcdefgh[2];
        double holding_double_hgfedcba[2];
    } holding_reg_params_t;
    #pragma pack(pop)

    // Enumeration of modbus slave addresses accessed by master device
    enum {
        MB_DEVICE_ADDR1 = 1, // Short address of Modbus slave device
        MB_SLAVE_COUNT
    };

  // Enumeration of all supported CIDs for device (used in parameter definition table)
    enum {
        CID_HOLD_U8_A = 0,
        CID_HOLD_U16_AB,
        CID_HOLD_UINT32_ABCD,
        CID_HOLD_FLOAT_CDAB,
        CID_HOLD_UINT64_ABCDEFGH,
        CID_HOLD_DOUBLE_HGFEDCBA,
        CID_COUNT
    };

    // Example Data Dictionary for to address parameters from slaves with different options of endianness
    mb_parameter_descriptor_t device_parameters[] = {
        // CID, Name, Units, Modbus addr, register type, Modbus Reg Start Addr, Modbus Reg read length, 
        // Instance offset (NA), Instance type, Instance length (bytes), Options (NA), Permissions
        { CID_HOLD_U8_A, STR("U8_A"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING, 
                HOLD_REG_START(holding_u8_a), HOLD_REG_SIZE(holding_u8_a),
                HOLD_OFFSET(holding_u8_a), PARAM_TYPE_U8_A, (HOLD_REG_SIZE(holding_u8_a) << 1), 
                OPTS( 0, UCHAR_MAX, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_HOLD_U16_AB, STR("U16_AB"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING, 
                HOLD_REG_START(holding_u16_ab), HOLD_REG_SIZE(holding_u16_ab),
                HOLD_OFFSET(holding_u16_ab), PARAM_TYPE_U16_AB, (HOLD_REG_SIZE(holding_u16_ab) << 1), 
                OPTS( 0, USHRT_MAX, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_HOLD_UINT32_ABCD, STR("UINT32_ABCD"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING, 
                HOLD_REG_START(holding_uint32_abcd), HOLD_REG_SIZE(holding_uint32_abcd),
                HOLD_OFFSET(holding_uint32_abcd), PARAM_TYPE_U32_ABCD, (HOLD_REG_SIZE(holding_uint32_abcd) << 1), 
                OPTS( 0, ULONG_MAX, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_HOLD_FLOAT_CDAB, STR("FLOAT_CDAB"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING,
                HOLD_REG_START(holding_float_cdab), HOLD_REG_SIZE(holding_float_cdab),
                HOLD_OFFSET(holding_float_cdab), PARAM_TYPE_FLOAT_CDAB, (HOLD_REG_SIZE(holding_float_cdab) << 1), 
                OPTS( 0, ULONG_MAX, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_HOLD_UINT64_ABCDEFGH, STR("UINT64_ABCDEFGH"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING,
                HOLD_REG_START(holding_uint64_abcdefgh), HOLD_REG_SIZE(holding_uint64_abcdefgh),
                HOLD_OFFSET(holding_uint64_abcdefgh), PARAM_TYPE_UINT64_ABCDEFGH, (HOLD_REG_SIZE(holding_uint64_abcdefgh) << 1), 
                OPTS( 0, ULLONG_MAX, 0 ), PAR_PERMS_READ_WRITE_TRIGGER },
        { CID_HOLD_DOUBLE_HGFEDCBA, STR("DOUBLE_HGFEDCBA"), STR("--"), MB_DEVICE_ADDR1, MB_PARAM_HOLDING,
                HOLD_REG_START(holding_double_hgfedcba), HOLD_REG_SIZE(holding_double_hgfedcba),
                HOLD_OFFSET(holding_double_hgfedcba), PARAM_TYPE_DOUBLE_HGFEDCBA, (HOLD_REG_SIZE(holding_double_hgfedcba) << 1), 
                OPTS( 0, ULLONG_MAX, 0 ), PAR_PERMS_READ_WRITE_TRIGGER }
    };
    uint16_t num_device_parameters = (sizeof(device_parameters) / sizeof(device_parameters[0]));

The example above describes the definition of just several extended types. The types described in the :ref:`modbus_mapping_complex_data_types` allow to address the most useful value formats from devices of known third-party vendors.
Once the type of characteristic is defined in data dictionary the stack is responsible for conversion of values to/from the corresponding type option into the format recognizable by compiler.

.. note:: Please refer to your vendor device manual and its mapping table to select the types suitable for your device.

The Modbus stack contains also the :ref:`modbus_api_endianness_conversion` - endianness conversion API functions that allow to convert values from/to each extended type into compiler representation.

During initialization of the Modbus stack, a pointer to the Data Dictionary (called descriptor) must be provided as the parameter of the function below. 

:cpp:func:`mbc_master_set_descriptor`:

Initialization of master descriptor. The descriptor represents an array of type :cpp:type:`mb_parameter_descriptor_t` and describes all the characteristics accessed by master.

.. code:: c

    static void *master_handle = NULL; // Must exist in the module and be initialized prior to call
    ....
    // Set master data dictionary for initialized master instance - master_handle
    ESP_ERROR_CHECK(mbc_master_set_descriptor(master_handle, &device_parameters[0], num_device_parameters));

The Data Dictionary can be initialized from SD card, MQTT or other source before start of stack. Once the initialization and setup is done, the Modbus controller allows the reading of complex parameters from any slave included in descriptor table using its CID.
Refer to :ref:`example TCP master <example_mb_tcp_master>`, :ref:`example Serial master <example_mb_master>` for more information.

.. _modbus_api_master_start_communication:

Master Communication
^^^^^^^^^^^^^^^^^^^^

The starting of the Modbus controller is the final step in enabling communication. This is performed using function below:

:cpp:func:`mbc_master_start`

.. code:: c

    static void *master_handle = NULL;  // Pointer to allocated interface structure
    ....
    esp_err_t err = mbc_master_start();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "mb controller start fail, err = 0x%x.", (int)err);
    }
    
The list of functions below are used by the Modbus master stack from a user's application:

:cpp:func:`mbc_master_send_request`:

This function executes a blocking Modbus request. The master sends a data request (as defined in parameter request structure :cpp:type:`mb_param_request_t`) and then blocks until a response from corresponding slave and returns the status of command execution. This function provides a standard way for read/write access to Modbus devices in the network.

.. note:: The function can be used to form the custom request with non-standard commands to resolve compatibility issues with the custom slaves. If it is not the case the regular API should be used: :cpp:func:`mbc_master_set_parameter`, :cpp:func:`mbc_master_get_parameter`.

:cpp:func:`mbc_master_get_cid_info`:

The function gets information about each characteristic supported in the data dictionary and returns the characteristic's description in the form of the :cpp:type:`mb_parameter_descriptor_t` structure. Each characteristic is accessed using its CID.

:cpp:func:`mbc_master_get_parameter`

The function reads the data of a characteristic defined in the parameters of a Modbus slave device. The additional data for request is taken from parameter description table.

:cpp:func:`mbc_master_get_parameter_with`

The function allows to read the data of a characteristic from any slave device addressed by `uid` parameter of the function instead of slave address defined in the data dictionary. In this case the ``mb_slave_addr`` field of the parameter descriptor :cpp:type:`mb_parameter_descriptor_t` shall be equal to ``MB_SLAVE_ADDR_PLACEHOLDER``. In case of TCP type of communication the connection phase should be completed prior call of this function.

Example: 

.. code:: c

    static void *master_handle = NULL;
    ....
    const mb_parameter_descriptor_t* param_descriptor = NULL;
    uint8_t temp_data[4] = {0}; // temporary buffer to hold maximum CID size
    uint8_t type = 0;
    ....
    // Get the information for characteristic cid from data dictionary
    esp_err_t err = mbc_master_get_cid_info(cid, &param_descriptor);
    if ((err != ESP_ERR_NOT_FOUND) && (param_descriptor != NULL)) {
        err = mbc_master_get_parameter(master_handle, param_descriptor->cid, (uint8_t*)temp_data, &type);
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "Characteristic #%d %s (%s) value = (0x%" PRIx32 ") read successful.",
                             param_descriptor->cid,
                             param_descriptor->param_key,
                             param_descriptor->param_units,
                             *(uint32_t*)temp_data);
        } else {
            ESP_LOGE(TAG, "Characteristic #%d (%s) read fail, err = 0x%x (%s).",
                            param_descriptor->cid,
                            param_descriptor->param_key,
                            (int)err,
                            (char*)esp_err_to_name(err));
        }
    } else {
        ESP_LOGE(TAG, "Could not get information for characteristic %d.", cid);
    }

:cpp:func:`mbc_master_set_parameter`

The function writes characteristic's value defined as `cid` parameter in corresponded slave device. The additional data for parameter request is taken from master parameter description table.

:cpp:func:`mbc_master_set_parameter_with`

The function is similar to previous function but allows to set the data of a characteristic in any slave device addressed by `uid` parameter of the function instead of the slave address ``mb_slave_addr`` field defined in the data dictionary. The corresponded ``mb_slave_addr`` field for the characteristic in the object disctionary shall be defined as ``MB_SLAVE_ADDR_PLACEHOLDER``. 

.. note:: When the TCP mode of communication is used the functions above additionally check the connection state of the slave being accessed and return error if the slave connection is not actual.

.. code:: c

        static void *master_handle = NULL;
        ....
        uint8_t type = 0;                   // Type of parameter
        uint8_t temp_data[4] = {0};         // temporary buffer
        // Read the characteristic from slave and save the data to temp_data instance
        esp_err_t err = mbc_master_set_parameter(master_handle, CID_TEMP_DATA_2, (uint8_t*)temp_data, &type);
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "Set parameter data successfully.");
        } else {
            ESP_LOGE(TAG, "Set data fail, err = 0x%x (%s).", (int)err, (char*)esp_err_to_name(err));
        }

.. _modbus_api_master_destroy:

Modbus Master Teardown
^^^^^^^^^^^^^^^^^^^^^^

This function stops Modbus communication stack and destroys controller interface and free all used active objects.  

:cpp:func:`mbc_master_destroy`

.. code:: c

    // Pointer to allocated interface structure, must be intitialized by constructor
    static void *master_handle = NULL;
    ...
    ESP_ERROR_CHECK(mbc_master_destroy(master_handle));
