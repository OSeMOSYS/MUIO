import { Message } from "../../Classes/Message.Class.js";
import { Base } from "../../Classes/Base.Class.js";
import { Html } from "../../Classes/Html.Class.js";
import { Model } from "../Model/RYTEM.Model.js";
import { Grid } from "../../Classes/Grid.Class.js";
import { Osemosys } from "../../Classes/Osemosys.Class.js";
import { GROUPNAMES } from "../../Classes/Const.Class.js";
import { DEF } from "../../Classes/Definition.Class.js";
import { MessageSelect } from "./MessageSelect.js";

export default class RYTEM {
    static onLoad(group, param) {
        Message.loaderStart('Loading data...');
        Base.getSession()
        .then(response => {
            let casename = response['session'];
            if (casename) {
                const promise = [];
                promise.push(casename);
                const genData = Osemosys.getData(casename, 'genData.json');
                promise.push(genData);
                const PARAMETERS = Osemosys.getParamFile();
                promise.push(PARAMETERS);
                const RYTEMdata = Osemosys.getData(casename, "RYTEM.json");
                promise.push(RYTEMdata);
                return Promise.all(promise);
            } else {
                let er = {
                    "message": 'There is no model selected!',
                    "status_code": "CaseError"
                }
                return Promise.reject(er);
                //throw new Error(JSON.stringify(er));
                //MessageSelect.init(RYTEM.refreshPage.bind(RYTEM));
            }
        })
        .then(data => {
            let [casename, genData, PARAMETERS, RYTEMdata] = data;
            if (RYTEMdata['EAR']['SC_0'].length == 0) {
                let er = {
                    "message": 'There is no activity defined!',
                    "status_code": "ActivityError",
                    "casename": casename
                }
                //throw new Error('Activity');
                return Promise.reject(er);
            }
            let model = new Model(casename, genData, RYTEMdata, group, PARAMETERS, param);
            this.initPage(model);
            this.initEvents(model);
        })
        .catch(error => {
            if (error.status_code == 'CaseError') {
                MessageSelect.init(RYTEM.refreshPage.bind(RYTEM));
            }
            else if (error.status_code == 'ActivityError') {
                MessageSelect.activity(RYTEM.refreshPage.bind(RYTEM), error.casename);
            }
            Message.loaderEnd();
            Message.warning(error);
        });
    }

    static initPage(model) {
        Message.clearMessages();
        //Navbar.initPage(model.casename);
        Html.title(model.casename, model.PARAMNAMES[model.param], GROUPNAMES[model.group]);
        Html.ddlParams(model.PARAMETERS['RYTEM'], model.param);
        let $divGrid = $('#osy-gridRYTEM');
        var daGrid = new $.jqx.dataAdapter(model.srcGrid);
        Grid.Grid($divGrid, daGrid, model.columns, {groupable: false, filterable: true, sortable:true});
        if (model.scenariosCount > 1) {
            Html.lblScenario( model.scenariosCount);
            Html.ddlScenarios(model.scenarios, model.scenarios[1]['ScenarioId']);
            Grid.applyGridFilter($divGrid, model.years);
        }
    }

    static refreshPage(casename) {
        Message.loaderStart('Loading data...');
        Base.setSession(casename)
        .then(response => {
            const promise = [];
            promise.push(casename);
            const genData = Osemosys.getData(casename, 'genData.json');
            promise.push(genData);
            const PARAMETERS = Osemosys.getParamFile();
            promise.push(PARAMETERS);
            const RYTEMdata = Osemosys.getData(casename, 'RYTEM.json');
            promise.push(RYTEMdata);
            return Promise.all(promise);
        })
        .then(data => {
            let [casename, genData, PARAMETERS, RYTEMdata] = data;
            if (RYTEMdata['EAR']['SC_0'].length == 0) {
                let er = {
                    "message": 'There is no activity defined!',
                    "status_code": "ActivityError",
                    "casename": casename
                }
                //throw new Error('Activity');
                return Promise.reject(er);
            }
            let model = new Model(casename, genData, RYTEMdata, 'RYTEM', PARAMETERS, PARAMETERS['RYTEM'][0]['id']);
            this.initPage(model);
            this.initEvents(model);
        })
        .catch(error => {
            setTimeout(function () {
                if (error.status_code == 'CaseError') {
                    MessageSelect.init(RYTEM.refreshPage.bind(RYTEM));
                }
                else if (error.status_code == 'ActivityError') {
                    MessageSelect.activity(RYTEM.refreshPage.bind(RYTEM), error.casename);
                }
                Message.warning(error.message);
            }, 500);
        });
    }

    static initEvents(model) {

        let $divGrid = $('#osy-gridRYTEM');

        $("#casePicker").off('click');
        $("#casePicker").on('click', '.selectCS', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            var casename = $(this).attr('data-ps');
            Html.updateCasePicker(casename);
            RYTEM.refreshPage(casename);
            Message.smallBoxConfirmation("Confirmation!", "Model " + casename + " selected!", 3500);
        });

        $("#osy-saveRYTEMdata").off('click');
        $("#osy-saveRYTEMdata").on('click', function (event) {
            event.preventDefault();
            event.stopImmediatePropagation();

            let param = $("#osy-ryt").val();
            let rytData = $divGrid.jqxGrid('getboundrows');
            let data = JSON.parse(JSON.stringify(rytData, ['ScId', 'TechId', 'EmisId', 'MoId'].concat(model.years)));

            let saveData = {};
            $.each(data, function (id, obj) {
                if (!saveData[obj.ScId]) { saveData[obj.ScId] = []; }
                saveData[obj.ScId].push(obj);
                delete obj.ScId;
            });

            Osemosys.updateData(saveData, param, "RYTEM.json")
            .then(response => {
                Message.bigBoxSuccess('Model message', response.message, 3000);
                //sync S3
                if (Base.AWS_SYNC == 1) {
                    Base.updateSync(model.casename, "RYTEM.json");
                }
            })
            .catch(error => {
                Message.bigBoxDanger('Error message', error, null);
            })
        });

        $("#osy-ryt").off('change');
        $('#osy-ryt').on('change', function () {
            Message.clearMessages();
            Html.title(model.casename, model.PARAMNAMES[this.value], GROUPNAMES[model.group]);
            model.srcGrid.root = this.value;
            $divGrid.jqxGrid('updatebounddata');
            model.param = this.value;
            Grid.applyGridFilter($divGrid, model.years);
            Html.lblScenario( model.scenariosCount);
            $('#definition').html(`${DEF[model.group][model.param].definition}`);
        });

        $("#osy-scenarios").off('click');
        $("#osy-scenarios").on('click', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
        });

        $("#osy-openScData").off('click');
        $("#osy-openScData").on('click', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            var sc = $("#osy-scenarios").val();
            Html.lblScenario(sc);
            Grid.applyGridFilter($divGrid, model.years, sc);
            Message.smallBoxInfo('Info', 'Scenario data opened!', 2000);
        });

        $("#osy-hideScData").off('click');
        $("#osy-hideScData").on('click', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            Html.lblScenario( model.scenariosCount);
            Grid.applyGridFilter($divGrid, model.years);
            Message.smallBoxInfo('Info', 'Scenario data hidden!', 2000);
        });

        $("#osy-removeScData").off('click');
        $("#osy-removeScData").on('click', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            var sc = $("#osy-scenarios").val();
            let rows = $divGrid.jqxGrid('getboundrows');

            $.each(rows, function (id, obj) {
                if (obj.Sc == sc) {
                    $.each(model.years, function (i, year) {
                        model.gridData[model.param][id][year] = null;
                    });
                }
            });

            model.srcGrid.localdata = model.gridData;
            $divGrid.jqxGrid('updatebounddata');

            Html.lblScenario( model.scenariosCount);
            Grid.applyGridFilter($divGrid, model.years);
            Message.smallBoxInfo('Info', 'Scenario data removed!', 2000);
        });

        let pasteEvent = false;
        $divGrid.bind('keydown', function (event) {
            pasteEvent = false;
            var ctrlDown = false, ctrlKey = 17, cmdKey = 91, vKey = 86, cKey = 67;
            var key = event.charCode ? event.charCode : event.keyCode ? event.keyCode : 0;
            if (key == vKey) {
                pasteEvent = true;
                setTimeout(function () {
                    let gridData = $divGrid.jqxGrid('getboundrows');
                    //update grid model
                    model.gridData[model.param] = gridData;
                }, 500);
            }
        }).on('cellvaluechanged', function (event) {
            if (!pasteEvent) {
                Pace.restart();
                var args = event.args;
                var year = event.args.datafield;
                var rowBoundIndex = args.rowindex;
                var value = args.newvalue;
                var techId = $divGrid.jqxGrid('getcellvalue', rowBoundIndex, 'TechId');
                var emisId = $divGrid.jqxGrid('getcellvalue', rowBoundIndex, 'EmisId');
                var moId = $divGrid.jqxGrid('getcellvalue', rowBoundIndex, 'MoId');
                var scId = $divGrid.jqxGrid('getcellvalue', rowBoundIndex, 'ScId');

                //update grid model
                $.each(model.gridData[model.param], function (id, obj) {
                    if (obj.TechId == techId && obj.EmisId == emisId && obj.ScId == scId && obj.MoId == moId) {
                        if (value) {
                            obj[year] = value;
                        } else {
                            obj[year] = 0;
                        }
                    }
                });
            }
        });

        let res = true;
        $("#resizeColumns").off('click');
        $("#resizeColumns").click(function () {
            if (res) {
                $divGrid.jqxGrid('autoresizecolumn', 'Sc');
                $divGrid.jqxGrid('autoresizecolumn', 'Tech');
                $divGrid.jqxGrid('autoresizecolumn', 'Emis');
            }
            else {
                $divGrid.jqxGrid('autoresizecolumns');
            }
            res = !res;
        });

        $("#xlsAll").off('click');
        $("#xlsAll").click(function (e) {
            e.preventDefault();

            let rytData = $divGrid.jqxGrid('getdisplayrows');
            let data = JSON.parse(JSON.stringify(rytData, ['Sc', 'Tech', 'Emis', 'MoId', 'UnitId'].concat(model.years)));

            Base.prepareCSV(model.casename, data)
            .then(response =>{
                Message.smallBoxInfo('Case study message', response.message, 3000);
                $('#csvDownload').trigger('click');
                window.location = $('#csvDownload').attr('href');
            })
            .catch(error=>{
                Message.bigBoxDanger('Error message', error, null);
            })
        });

        $("#decUp").off('click');
        $("#decUp").on('click', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            model.d++;
            model.decimal = 'd' + parseInt(model.d);
            $divGrid.jqxGrid('refresh');
        });

        $("#decDown").off('click');
        $("#decDown").on('click', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            model.d--;
            model.decimal = 'd' + parseInt(model.d);
            $divGrid.jqxGrid('refresh');
        });

        $("#showLog").off('click');
        $("#showLog").click(function (e) {
            e.preventDefault();
            $('#definition').html(`${DEF[model.group][model.param].definition}`);
            $('#definition').toggle('slow');
        });

        Message.loaderEnd();
    }
}