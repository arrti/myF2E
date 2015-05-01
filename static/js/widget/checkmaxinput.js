/**********************************************************************************************************
调用方式
<textarea type="text" id="description" name="description" placeholder="" class="input-xlarge"
 onkeydown="checkMaxInput(this,50)" onkeyup="checkMaxInput(this,50)"
 onfocus="checkMaxInput(this,50)" onblur="checkMaxInput(this,50);resetMaxmsg()"></textarea>
************************************************************************************************************/

//多行文本输入框textarea剩余字数计算
        function checkMaxInput(obj, maxLen) {
            if (obj == null || obj == undefined || obj == "") {
                return;
            }
            if (maxLen == null || maxLen == undefined || maxLen == "") {
                maxLen = 100;
            }

            var strResult;
            var $obj = $(obj);
            var newid = $obj.attr("id") + 'msg';

            if (obj.value.length > maxLen) { //如果输入的字数超过了限制
                obj.value = obj.value.substring(0, maxLen); //就去掉多余的字
                strResult = '<span id="' + newid + '" class=\'Max_msg\' ><br/>还能输入' + (maxLen - obj.value.length) + '字</span>'; //计算并显示剩余字数
            }
            else {
                strResult = '<span id="' + newid + '" class=\'Max_msg\' ><br/>还能输入' + (maxLen - obj.value.length) + '字</span>'; //计算并显示剩余字数
            }

            var $msg = $("#" + newid);
            if ($msg.length == 0) {
                $obj.after(strResult);
            }
            else {
                $msg.html(strResult);
            }
        }

        //清空剩除字数提醒信息
        function resetMaxmsg() {
            $("span.Max_msg").remove();
        }